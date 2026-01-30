---
layout: post
tags: [cs, musing]
published: true
title: 함부로 unsigned를 쓰지 말아야 할 이유
---

### 수정 (2021/09/30)
글의 방향이 원래 의도와 다르게 "무조건 unsigned를 쓰지 말자"로 읽히는 것 같아서, 내용을 좀더 보강해보았다. (Special thanks to [kkeun.net](https://kkeun.net)!)

어쩌다가 C의 타입 캐스팅, 특히 `unsigned`와 관련된 걸 찾아보게 되었는데... 납득이 가긴 하지만 시간이 지나서 보면 100% 헷갈릴 것이기 때문에 (...) 짧게 기록해둔다.

## Integral Promotion
`char`, `short` 뿐 아니라 `unsigned`나 `enum` 타입은 expression에서 `int` 타입으로 승격(promotion)되어서 실제 연산에 쓰인다. 예를 들면, binary operation과 bit-shift operation에서 이 타입들이 연산에 쓰이면, 일단 `int` 형으로 캐스팅되고 나서 계산이 이루어지고 이 `int` 결과 값을 최종 변수에 담는다.

Integer Promotion이라고도 한다.

## Zero/Sign Extension
메모리 표현이 작은 타입(e.g. `char`)을 더 큰 타입(e.g. `int`)에 담으려면, 작은 타입에 비어있는 비트를 큰 타입에 맞게 확장해야 한다. 이때 **부호**에 맞게 채워야 한다. 만약 작은 타입의 값이 양수라면 그냥 `0`으로 다 채우면 되지만(Zero Extension), 음수라면 2의 보수법을 따라야 하므로 `1`로 채우게 된다(Sign Extension).

예를 들어, 10비트 음수 값인 `11 1111 0001` (즉 `-15`)를 16비트에 담으려면 비어있는 6비트만큼을 모두 `1`로 채워서 `1111 1111 1111 0001`로 확장해야지만 16비트에서 `-15`를 표현하는 정확한 2의 보수가 된다.

---

이 두 가지 행동 각각은 납득이 가긴 한다. 하지만 이걸 고려하지 않고 `unsigned`를 쓰다보면 의도치 않은 동작을 일으킬 수 있다.

---

```c
unsigned char p = 0xff;
unsigned long long res = p << 24;
// expected: 0x0000 0000 ff00 0000
// actual  : 0xffff ffff ff00 0000

printf("Expected value: %lu, Actual value: %lu\n", 0x00000000ff000000, res);
// Expected value: 4278190080, Actual value: 18446744073692774400
```

`p`의 타입이 `unsigned char`이지만, bit-shift 계산을 위해 `int` 형으로 integral promotion 된다. 그래서 `p << 24`는 `0xff00 0000`를 담은 32비트 정수값이 되어버린다. 여기까진 좋다.

하지만 이 최종 값을 `unsigned long long` 타입에 담을 때 sign extension이 발생하게 된다. 먼저 `int` 타입의 `0xff00 0000`은 MSB가 1이므로 2의 보수 표기법에 따라 이를 **음수**로 해석하게 되고, 모자란 32비트를 모조리 `1`로 채운다. 따라서 결과 값은 `0xffff ffff ff00 0000`이 되어 버린다. 그 이후 `unsigned`가 적용되므로, `res`의 값은 엄청나게 큰 값이 되어버린다. 값을 찍어보면 기대했던 `0x0000 0000 ff00 0000`보다 엄청나게 큰 값을 볼 수 있다.

현실에서는 이 값이 복잡한 경로(e.g. 입력)로 들어오기 때문에, 곧바로 확인하기가 어렵다. 거기다 이렇게 들어온 값이 직접 쓰이게 되면 경우에 따라 *가끔씩* 의도치 않은 동작을 할 수 있어서 더 헷갈린다.

위의 코드를 좀더 꼬아서 다음과 같은 경우를 생각해보자.


```c
unsigned char p = 0xff;  // maybe from input
unsigned long long k = 0x00000000ff000000; // save correct value
printf("p << 24: 0x%016lx, k: 0x%016lx\n", p << 24, k);
// p << 24: 0x00000000ff000000, k: 0x00000000ff000000
// print the same representation!

if ( (p << 24) > k) {
  printf("You shall not reach here!\n");
}
```

디버깅을 위해 값을 하나씩 찍어보면, `p << 24`의 값은 `0`이 잘 채워진 `0x0000 0000 ff00 0000`이 나온다. 그러므로 `(p << 24) > k`의 결과는 `false`가 되어 브랜치 안의 `printf`에 도달하지 못할 거라는 예측은 언뜻 그럴듯하다. 하지만 실제로 이 코드를 컴파일해서 실행하면 "You shall not reach here!" 메시지가 뜬다. 각각을 출력할 때에는 의도한 결과가 나왔지만, `(p << 24) > k`를 계산하는 과정에서 sign extension이 발생하여 의도치않게 저기에 도달하고 만 것이다.

---

대부분의 언어/하드웨어에서는 음수의 표현으로 2의 보수법을 쓰고, 또 학교에서 가르치기도 해서, 일반적으로 `signed`의 동작 방식은 잘 받아들여진다. 하지만 `unsigned`는 추가적인 해석이 필요하기 때문에, 왜 이렇게 동작하는지 잘 알아두지 않으면 헷갈릴 수 밖에 없다. `unsigned`는 보통 절대 음수가 될 수 없는 값을 표현하거나, 혹은 비트 연산을 할 때 많이 사용하기 때문에(왜 그럴까?), C/C++ 또는 Rust와 같은 로우 레벨의 시스템 프로그래밍 언어에서 필요한 도구인 것은 분명하다. 하지만, 추가적인 복잡함을 고려하지 않고 아무 생각없이 `unsigned`를 쓰다가는, 이처럼 의도치 않은 동작을 마주할 가능성이 높다.


개인적으로는 "정말 `unsigned` 타입이 필요할까?"에 대한 확신이 없다면, 그냥 `unsigned`를 쓰지 않는 것이 좋아보인다. `signed`의 동작은 우리 프로그래머에게 친숙하고, 여기서 설명한 암묵적인 상황에서는 `signed`로 취급되는 경우가 많아서, 이상하게 동작하더라도 우리에게 익숙한 방향으로 동작할테니 말이다.

좀더 솔직하게 말하자면, 가능하면 이런 복잡하고 헷갈리는 코너 케이스를 애초부터 고려하지 않아도 되는 언어를 쓰는 것이 좋다. 예를 들면 OCaml 이라던가, OCaml 이라던가 ... 😅
