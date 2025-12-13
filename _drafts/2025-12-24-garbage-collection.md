---
layout: post
published: true
tag: [dev, ocaml, essay]
title: 가비지 컬렉션 이야기
---

## 목차
{:.no_toc}

* Table of contents
{:toc}


모든 프로그램은 반드시 메모리가 필요하다.

자동으로 관리되는 스택은 제한된 크기가 작다. 보통 윈도우는 1MB이고 리눅스는 8MB다. 더 큰 크기의 계산을 하려면 스택을 벗어나 힙 메모리가 필요하다. 프로그램은 커널에게 부탁해서 힙 메모리를 얻는다. 그리고 다 사용한 메모리는 다시 커널에게 돌려줘야 한다. 가상 메모리도 물리 메모리도 모두 유한한 자원이기 때문이다. 제때 안돌려주고 계속 메모리를 얻기만 하면 계속된 페이징, 스와핑, 페이지 폴트, 쓰레싱(Thrashing) 등의 이유로 성능이 계속 곤두박질치다가 결국 커널은 패닉에 빠질 것이다.

그래서 보통은 프로그래머가 직접 메모리를 관리하는 코드를 작성한다. 필요한 만큼 커널에게 할당받아서 쓰고, 다 쓰고 나면 다시 커널에게 돌려준다. 이것이 기본이다. 그러나 프로그램의 요구사항이 복잡해지고 예외 처리와 같은 프로그래밍 언어의 고급 기능이 많아질수록 메모리 관리는 복잡해진다. 무엇보다 중요한 것은, 사람은 실수를 저지른다. 커널에게 받은 메모리를 돌려줬는데 아직 유효한 줄 알고 잘못된 메모리를 사용해버리거나 (Use After Free), 까먹고 돌려주지 않거나 (Memory Leak), 같은 메모리를 여러 번 돌려주는 (Double Free) 등의 실수는 너무도 흔해서 각각에 이름이 붙을 정도다. 그리고 이들은 대부분 적어도 프로그램 성능의 발목을 잡아 느려지게 만들거나, 치명적인 보안 취약점이 되거나, 프로그램을 죽여버린다.

그래서 자동으로 메모리를 관리하는 방법이 연구되기 시작한다. 최초의 자동 메모리 관리 방법은 1959년에 LISP 프로그래밍 언어에 도입되었다. LISP의 창시자이자 인공지능 연구자 존 매카시 님의 [관련 논문](https://www-formal.stanford.edu/jmc/recursive.pdf)의 27페이지에는 지금의 트레이싱 컬렉터(Tracing Collector)에 대한 기초적인 아이디어, 즉 *프로그램의 어떤 부분에서도 찾을 수 없는(닿을 수 없는) 데이터는 버려진 것으로 간주하고 나중에 재활용하는 방법*을 설명하고 있다.

> ... Such a register may be considered abandoned by the program because its contents can no longer be found by any possible program; hence its contents are no longer of interest, and so we would like to have it back on the free-storage list. ...

참고로 7번 주석에는 다음과 같은 재밌는 주석이 달려있는데:

> We already called this process "garbage collection", but I guess I chickened out of using it in the paper - or else the Research Laboratory of Electronics grammar ladies wouldn't let me.

겁을 먹고 논문에서는 딱 한번만 등장한 "가비지 컬렉션"이라는 이름이 정작 지금은 표준적인 개념으로 널리 쓰이고 있다는 사실이 아이러니하다.

# 왜 필요할까?
"애초에 가비지 컬렉션이 왜 필요함? 처음부터 메모리 이슈 없게 잘 짜면 되는 거 아님?" 이라고 생각하기 쉽다. 나도 그랬다. 하지만 (꼭 가비지 컬렉션이라는 방법이 아니더라도) 메모리 관리를 위한 다양한 방법론이 여전히 연구 되고 있는 데에는 다 이유가 있다.

## 과거와 현재

먼저 역사적인 배경을 한번 살펴보자. 최초의 가비지 컬렉션이 LISP 언어에 도입된 이유 중 하나로, 당시 ALGOL과 같은 프로그래밍 언어에서 댕글링 포인터 문제, 그러니까 (어떤 이유에서든) 쓰던 메모리를 이미 해제했는데 그걸 모른채로 메모리 주소를 계속 갖고 있다가 나중에 잘못 사용해버려서 결국 Use After Free 버그로 나타나는 문제가 심각한 이슈로 떠올랐다는 것이 있다. 그 당시 프로그래머라면 정말 똑똑한 소수의 선택된 사람들일텐데, 그런 친구들에게도 수동으로 메모리를 관리하는 일은 쉽지 않았던 것이다.[^1]

[^1]: 물론 최초의 가비지 컬렉션은 여러가지 한계로 인해 "너무 느리다"는 비판을 받긴 했지만, 이것이 씨앗이 되어서 지금은 많은 언어에 표준적인 기능으로 자리잡았다.

**근데 이 문제는 현재도 해결되지 않았다.** 오히려 인터넷이 발전하면서 더 심각해졌다. Use After Free 버그는 이제 프로그램이 죽는 데서 그치지 않고 더 큰 문제를 만든다. 인터넷이 발전하면서 정말 많은 것들이 가능해졌지만, 그와 동시에 프로그램의 보안 취약점이 더 이상 단순한 문제가 아니게 되었다. [마이크로소프트의 한 조사](https://www.microsoft.com/en-us/msrc/blog/2019/07/we-need-a-safer-systems-programming-language)에 따르면 매년 CVE (공개적으로 알려진 보안 취약점에 아이디를 붙이는 시스템) 의 약 70%가 메모리 안전정 문제라고 한다. [구글에서도 비슷한 결과](https://www.zdnet.com/article/chrome-70-of-all-security-bugs-are-memory-safety-issues/)를 발표한 적이 있는데, 크롬의 심각한 보안 관련 버그 중 70%가 메모리 관련 오류, 그 중 절반이 Use After Free였다고 한다.

1960년대에 발견된 문제가 2020년대에도 여전히 보안 취약점의 대다수를 차지한다는 건 수동 메모리 관리가 정말로 어렵다는 걸 말해준다. 게다가 이 단순해 보이는 메모리 오류가 프로그램의 보안에 구멍을 뚫리게 하고 이로 인해 정말로 상상도 못할 피해를 끼칠 수도 있게 된 것이다.

## 문제의 난이도

"메모리 이슈 없게 잘 짜면 되는 거 아님?"이 얼마나 어려운지를 보여주는 또 다른 명확한 근거는 바로 이 문제 자체의 본질적인 난이도이다. 메모리 오류의 대부분은 결국 커널로부터 힙 메모리를 할당 받아서 (`malloc`) 쓴 다음에 이걸 적절한 타이밍에 돌려줘야 (`free`) 하는 이 *타이밍*이 어긋나서 발생하는 것이다. 메모리를 할당하고 돌려주는 시점은 정확하게 알아낼 수 없다. 즉, "여기서 할당되어서 사용되던 메모리가 코드의 여기에서 딱 사용이 끝날테니 여기다가 `free`를 넣으면 되겠다" 라는 분석이 이론적으로 **불가능**하다. 좀더 구체적으로는 코드만 봐서는 할당된 메모리의 수명을 알아내는 알고리즘은 만들 수 없다 (Undecidable).[^2] 그렇다고 프로그램이 끝나는 시점에 한꺼번에 메모리를 돌려줘버리면 애초에 메모리를 관리하려는 의미가 없지.

[^2]: 그래서 Rust의 경우 언어의 표현력을 제한해서 이 문제를 결정 가능한 수준으로 축소해서 풀고, 컴파일러가 추론이 불가능하면 프로그래머에게 명시적인 라이프타임 어노테이션을 떠맡긴다.

그럼 문제를 조금 더 쉽게 줄여서, "이 메모리는 크기는 이 정도 되고 수명은 이 정도 된다" 라는 정보가 미리 알려져 있을 때 얘네들을 잘 배치해서 메모리 사용량을 최소화 하도록 하는 *동적 스토리지 할당 (Dynamic Storage Allocation, DSA)* 문제를 생각해볼 수 있다. 근데 이 문제는 NP-Complete 임이 증명되어 있다. 즉, 메모리를 잘 배치해서 최소한의 메모리만 사용하도록 계산하는 알고리즘이 있긴 있는데, 언제 끝날지 모른다. 이는 메모리의 생명주기가 (Lifetime) "이미 알려져 있는" 경우에도 최적의 배치를 찾는 것이 어렵다는 말이다. 아무튼 간에 메모리를 할당하고 돌려주는 타이밍을 맞추는 문제가 엄청나게 어렵다는 뜻이다.


## 인지적 부하

내가 더 중요하게 생각하는 점 중 하나는 바로 인지적인 부하이다 (Cognitive Load). 이제 현대의 복잡한 대규모 소프트웨어를 혼자서만 개발하는 것은 굉장히 어렵다. 설령 작은 규모를 혼자서 만들더라도 현재의 나와 미래의 나는 다른 사람이다. **코드는 쓰이는 것보다 훨씬 더 많이 읽힌다**. 관련해서 많은 격언들이 있다. 엉클 밥의 "읽기와 쓰이게 소요되는 시간의 비율은 10:1을 훨씬 상회한다" 라던지, 귀도 반 로썸의 "코드는 쓰이는 것보다 더 자주 읽힌다" 라던지. 그래서 어떤 코드 베이스를 이해하는 작업은 어렵다. 어떤 코드 한 줄을 이해하려고 한다고 하자. 만약 지금 보고 있는 코드가 속한 함수나 파일만이 아니라, 코드 베이스 전체, 심지어는 프로젝트가 사용하고 있는 라이브러리를 다 따라가서 연관된 모든 것들을 다 고려해야 한다면 (Global Reasoning) 결코 쉽지 않을 것이다. 그런데 만약 따라가서 살펴봐야 할 코드가 적은 지역적인 추론만이 필요하다면 (Local Reasoning), 이 작업은 한결 수월해질 수 있다.

진정한 의미의 "모듈화된 프로그래밍 (Modular Programming)"에서 가비지 컬렉션은 필수적이다. 모듈 사이에 의존성이 어쩔 수 없이 생길 수는 있다. 하지만 모듈이 동적으로 메모리를 할당하고 사용해야만 할 때, 이 메모리의 소유권 (Ownership) 분쟁이 발생하게 된다. 특히 모듈이 사용하는 객체가 여전히 쓰이는지는 보통 지역적인 속성이 아니라 **전역적인 속성**이다. 예를 들어, 모듈 A가 할당하는 어떤 객체를 모듈 B와 C가 공유하게 되면, 이 세 모듈을 모두 추적해야만 이 객체를 언제 할당할지 알 수 있다. 이렇게 모듈의 사용 방법 뿐만 아니라 모듈이 할당하는 메모리도 고려해야 한다면, 원래는 지역적으로 이해 가능하고 유연하게 조합하기 위해서 만들어진 모듈식 프로그래밍인데도 불구하고, 전역적으로 모듈이 사용하는 메모리를 관리하고 생존 여부를 추적해야 하기 때문에 추상화가 어그러뜨려지고 이해에 방해를 받게 된다. 게다가 이런 관리 작업을 추가로 구현하다 보면 런타임에서 비용도 상당할 수 있고, 멀티 쓰레드 어플리케이션이면 동기화도 고려해야 한다. 아무튼 간에 복잡해진다.

결국 언어 설계는 안전성, 표현력, 성능, 사용성 사이의 트레이드오프를 고려해야 한다. 가비지 컬렉션은 약간의 성능을 희생하면서 안전성, 표현력, 사용성을 모두 챙겨갈 수 있는 좋은 선택지이다.

# 추상화
그럼 이제 가비지 컬렉션에 대해서 하나씩 알아보자.

먼저 존 매커시의 설명을 현대적으로 한글로 풀어 쓰면 다음과 같다: "프로그램의 어디에서도 사용하지 않는 메모리는 가비지로 간주하고 따로 모아뒀다가 나중에 재활용한다." 이로부터 가비지 컬렉션을 아주 추상적인 두 단계로 나눌 수 있다.
 1. **가비지 찾기 (Garbage Detection)**: 살아있는 객체와 (Live Object, Reachable Object) 쓰이지 않는 가비지를 어떤 식으로든 구별한다.
 2. **가비지 수집 (Garbage Collection)**: 가비지 객체의 메모리를 수집한다. 곧바로 커널에게 돌려줄 수도 있고, 아니면 따로 모아놨다가 재활용할 수도 있다.

실제로 이 두 단계는 완전히 구분되지 않고 얽혀 있을 수 있고, 특히 수집 방법은 찾는 방법에 크게 의존하는 경우가 많다.

크게 두 갈래로 나뉜다. 각 객체의 참조 횟수를 추적해서 0이 되면 즉시 수집하는 **레퍼런스 카운팅**과, 주기적으로 지금 쓰고 있는 객체와 안쓰는 가비지를 구분하여 가비지만을 수집하는 **트레이싱 컬렉션**이 있다.

# Reference Counting
레퍼런스 카운팅은 앞의 두 단계를 다음과 같이 구현한다.
 1. 가비지 찾기: 각 객체의 참조 횟수를 유지하면서 프로그램이 실행되는 동안 객체를 참조하면 횟수를 늘리고 다 쓰면 줄이다가 0이되는 즉시 가비지로 판단한다.
 2. 가비지 수집: 참조 횟수가 0이 되는 즉시 관련된 객체의 모든 메모리를 수집한다.

이 방식의 특징은 위의 1, 2가 동시에 일어난다는 점이다.

레퍼런스 카운팅은 여러가지 장점과 단점이 있다. 장점으로는 메모리(객체)를 다 쓴 *즉시* 수집하기 때문에 객체의 수명이 명확해서 메모리를 되도록 필요한 만큼만 사용하는 편이고, 종료 처리도 (Finalise) 예측한 대로 동작한다. 그리고 통상적으로 메모리 관리의 응답 시간이 짧아서 응답성이 좋은 편이라 주로 실시간 시스템에서 채택된다. 그리고 생각보다 구현도 간단하다...고 하는데, CPython 구현 코드에서 레퍼런스 카운터를 [늘리거나](https://github.com/search?q=repo%3Apython%2Fcpython%20py_incref&type=code) [줄이는](https://github.com/search?q=repo%3Apython%2Fcpython+py_decref&type=code) 코드를 검색하면 엄청 많은 곳에서 발견되어서, 그렇게 쉬울 거라는 생각은 들지 않는다.

그런데 실제로 주변을 둘러보면 레퍼런스 카운팅**만** 가비지 컬렉션으로 도입한 언어나 프로그램은 잘 없다. 그 이유는 다음과 같은 여러 근본적인 한계 때문이다.

## 정확성의 한계

가장 큰 한계는 바로 그 유명한 순환 참조(Circular Reference)다. 두 객체가 서로 참조해버리면 이 객체(들)을 사용하던 곳이 일을 다하고 소멸되어도 여전히 참조 횟수가 1 이상이라서 절대로 수집되지 않는다 (Memory Leak). 이런 데이터가 얼마나 많겠냐 싶겠지만 실제로 생각보다 많다. 예를 들면 LRU 캐시에 사용되는 더블 링크드 리스트의 구현이나, 혹은 편의를 위해 부모 노드로 가는 포인터를 추가한 트리 노드 등은 꽤 자주 쓰인다. 그래서 파이썬과 같은 레퍼런스 카운팅 기반 가비지 컬렉션 언어에서는 추가적으로 트레이싱 컬렉터도 백업으로 실행하면서 이런 가비지를 따로 수집한다.

## 성능 오버헤드

또, 생각보다 오버헤드가 크다는 점이 있다. 일단 모든 객체에 "레퍼런스"라는 것을 도입해야 하는데, 말 그대로 **모든** 객체, 즉 언어가 제공하는 원시 데이터 타입 외에 사용자가 정의하는 것까지 포함해야 하기 때문에 객체를 표현하는데 제약이 생긴다. 그래서 보통 레퍼런스를 포함한 메타데이터 정보를 담는 일종의 박스 객체를 만들고 그 안에 메모리 공간을 동적 할당해서 실제 데이터를 (원시 타입이나 사용자 정의 타입) 담는데, 이걸 박싱된 객체 (Boxed) 라고 한다. 이로 인해 두 가지 오버헤드가 발생한다. 일단 정말 관심있는 데이터에 접근하려면 포인터를 따라가야 하는데, [가상 메모리 구조의 한계](../virtual-memory)로 인해 메모리를 따라가는 연산은 캐시 지역성에 좋지 못해서 느리다.

그리고 객체에 접근하는 모든 작업에 추가적으로 레퍼런스를 관리하는 연산을 해야하는데, 객체가 생성될 때는 물론이고, 어떤 객체가 담고있던 객체가 다른 객체로 바뀌면 한 객체의 레퍼런스는 늘이고 한 객체는 줄인 다음 0이 되었는지 확인해야 한다. 그래서 프로그램의 작업량 자체가 크면 여기에 비례해서 오버헤드도 늘어난다. 게다가 어떤 커다란 객체의 카운트가 0이 되어서 그 객체를 따라 연결된 수많은 객체들이 모두 다 해제되어야 하는 상황이 오게 되면, 일관되고 예측 가능한 성능이 깨진다는 점도 무시할 수 없다.

## 메모리 재사용의 어려움

다른 오버헤드로는 메모리 재사용이 어렵다는 점이 있다. 레퍼런스가 0이 된 객체의 메모리를 즉각 회수하지 않고 프리 리스트 (Free List) 같은 곳에 잠깐 관리했다가 나중에 재사용하려고 한다면, 이 커다란 객체의 해제 시점에서 모든 연결된 객체들을 다 따라가서 이것들을 일일이 다 프리 리스트에다가 넣어야 하고, 나중에 객체가 생성될 때 이 프리 리스트에서 지금 필요한 적당한 크기의 메모리를 가져와서 초기화를 해줘야 하는 등의 피할 수 없는 오버헤드가 **즉시** 발생한다. 게다가 프리 리스트를 도입해버리면 사실상 트레이싱 컬렉터의 특징을 갖게 되는데, 이러면 원래 장점이었던 응답성이라던지 예측 가능한 종료 처리도 잃어버리게 된다.

## 병렬 처리

개인적으로 겪었던 단점 중 하나는 바로 **객체를 읽는 모든 연산이 쓰기 연산이 되어버린다**는 것이었다. 이로 인해서 데이터를 단순히 읽기만 하는 것이 원천적으로 불가능하다. 예를 들어 커다란 데이터 덩어리를 여러 프로세스 사이에 읽기만 하는 목적으로 공유하는 경우, 커널이 제공하는 최적화 중 하나인 쓰기 시 복사(Copy-on-Write)를 적용하는 것이 불가능해져서 예상했던 것보다 엄청나게 많은 메모리를 잡아먹게 된다. 그래서 병렬 처리가 불가능했던 적이 있다. 이럴 때는 데이터를 곧바로 로딩하기 보다는 다른 라이브러리를 이용해서 읽기만 할 데이터를 공유 메모리에 올리는 방법으로 우회해야 한다.

최적화를 못받는다는 점 외에도 "읽기가 곧 쓰기"가 되는 특성으로 인해서 공유 메모리 병렬 처리 (Shared Memory Parallelism), 다시 말해서 멀티 쓰레드 환경에서의 런타임의 구현이 어려워진다. 여러 개의 프로세스/쓰레드가 공유된 오브젝트를 "읽기"만 해도 카운터를 "쓰게" 되는데, 이로 인해 경쟁 상태를 피하기 위해 (Race condition) 반드시 동기화가 필요하다. 그래서 이를 간단하게 하기 위해서 파이썬은 GIL(Global Interpreter Lock)을 도입하기도 했다.

## 레퍼런스 카운팅의 현재

이러한 한계들로 인해서 현대에는 레퍼런스 카운팅만을 도입한 언어는 잘 없다.
 * 하이브리드 접근: 레퍼런스 카운팅을 기본으로 하되, 순환 참조를 피하기 위해서 보조 트레이싱 컬렉션을 도입한다. 예를 들면 파이썬과 스위프트가 있다.
 * 제약된 레퍼런스 카운팅: 순환 참조를 방지하도록 소유권 규칙을 강제한다. Rust의 `Rc<T>`가 있다.

그리고 메모리를 재사용할 수 없다는 점으로 인해 최적화할 여지가 많지 않아서, 가비지 컬렉션과 관련된 많은 연구는 주로 아래에 설명할 트레이싱 컬렉션 위에서 진행되는 편이다.

# Tracing Collection
트레이싱 컬렉션, 말 그대로 따라가서 수집하는 가바지 컬렉션이 내가 좋아하는, 이제부터 풀어 볼 엑스트라 라지 스토리의 주제다.

이 방법은 앞에서 설명한 가비지 컬렉션 추상화의 두 단계, 즉 (1) 가비지를 추적하고 (2) 가비지를 수집하는 것을 정직하게 구분한다.

## Preliminaries

### 기본적인 개념: Tri Colour
트레이싱 컬렉션은 기본적으로 세 가지 색깔을 도입해서 객체의 상태를 구분한다.
 1. 흰색: GC 대상임. Reachable.
 2. 검은색: 살아남은 애들. live object
 3. 회색: GC의 탐색에 의해 방문(Reached)했지만 아직 그 자식들까지 다 확인하지는 못한 중간 상태.

즉 GC가 시작되면 처음에 객체는 전부 흰색. 그리고 객체를 하나씩 방문하면서 회색으로 칠해지고 자식 객체로 넘어갈 때 부모 객체는 검은색으로 칠해지면서 자식은 회색이 됨. 즉 흰색 -> 회색 -> 검은색 순으로 색이 진해지고. 따라갈 수 있는 모든 객체를 다 따라가서 색깔을 다 칠하고 나면, 검은색 객체는 살아남고 흰색 객체는 다 수집되어서 재활용됨.

### Boxing
앞에서 레퍼런스 카운팅이 참조 횟수를 세어야해서 객체마다 박싱이 필요하여 오버헤드가 발생한다고 했는데. 사실 이건 트레이싱도 마찬가지다. 객체마다 세 가지 색깔을 기록하려면 해시 테이블을 갖고 있던지 박싱하던지 둘 중 하나밖에 없다. 그래도 수많은 연구를 통해 트레이싱 컬렉션만을 위한 효율적인 박싱 방법이 개발되어왔다. 예를 들면 [현대의 가상 메모리 시스템의 특징](../virtual-memory)을 이용해서 모든 메모리 주소가 짝수임을 이용하여 최하위 비트가 0인지 1인지에 따라서 주소값을 따라 박싱된 값인지 아니면 어떤 원시적인 값인지를 판별할 수 있음.

### Collector와 Mutator
Very charmingly, GC researchers call the user program "mutator", because it mutates the memory states.

철저하게 가비지 컬렉션 입장에서 이름 지은 거라서 웃겼다.

### Weak Pointer
Weak pointers are like pointers, except that references from weak pointers do not prevent GC, and weak pointers must have their validity checked before they are used.

Weak pointers interact with the GC because the memory to which they refer may in fact still be valid, but containing a different object than it did when the weak pointer was created. Thus, whenever a garbage collector recycles memory, it must check to see if there are any weak pointers referring to it, and mark them as invalid (this need not be implemented in such a naive way).

A pointer to an object which does not prevent from being reclaimed. If the only pointers to an object are from weak references, the object may disappear, in which case the reference is replaced with some distinguished value, typically a language's equivalent of a NULL pointer. Weak references are often used for implementing caches.

### Ephemeron
GC의 두 개의 연결된 문제를 해결하기 위해 도입된 데이터 구조임. 하나는 이 객체가 수집되기 직전에 알림을 줌. 다른 하나는 어떤 객체를 참조하지 않고도 그 객체와 데이터를 연결할 수 있도록 해서 객체가 가비지 컬렉션되는 것을 방지함 (이게 대체 무슨말?). 논리적으론 키-값 쌍이고 키는 에피메론이 보호하는 객체로 수집될 때 시스템에 알림. 값은 임의의 데이터이고 비어있을 수 있음. GC에 의해 특별하게 처리됨.

### Finaliser
레퍼런스 카운팅과 달리 객체가 수집되는 시점을 정확하게 알 수 없기 때문에 Finaliser 구현이 까다로움. (좀더 조사 필요)

Finalisation, or destruction, is problematic. It is generally useful, but people disagree on how certain and timely it should be. The difficulty here is that in practice, no garbage collector provides an absolute guarantee that it will detect every single instance of unreachable storage in a bounded amount of time. Some GC designs deferred collection of regions of memory likely to contain mostly live memory, some can be "fooled" by bit patterns stored in integers, and in some cases artefacts of compilation (such as register use and calling conventions) will keep memory allocated long after it "should be" recycled. Reference counting is not immune to this problem; overflowed reference counts and cycles can both prevent collection, and some reference counting algorithms defer collection.

Yet another problem with finalisation is the difficulty of defining a proper order for finalisation. There are numerous problems, none with a clean solution.

For instance, it makes a certain amount of sense to finalise objects with zero direct references first, discard those, and continue finalising the new set of objects with zero direct references. That is, finalise in topological order. This has two problems, one in theory, one in practice. In theory, of course, *a cycle in the graph of objects* to be finalised will prevent a topological sort from succeeding. In practice, the "right" thing to do appears to be to signal an error (at least when debugging) and let the programmer clean this up. People with experience on large systems report that such cycles are in fact exceedingly rare (note, however, that some languages define "finalisers" for almost every object, and that was not the case for the large systems studied - there, finalisers were not too common).

The practical problem is that *finalisers can "revive" dead objects*. Dead objects can certainly refer to live objects, and it is also entirely possible for the code in a finaliser to store a pointer to a currently-dead object into a live object, thus reviving the "dead" object, perhaps even the object on whose behalf the finaliser was being run. This means either that a write barrier must be enforced so that this can be detected, or that after each GC, only those objects that have zero references can be finalised; the rest (those that ought to have zero references after the first batch is recycled) must wait for a subsequent GC. Write barriers are not always an option, and deferring finalisation more or less guarantees that more memory will be consumed and that resources will be slowly reclaimed.

The other approach is to declare that finalisers can be run in any order whatsoever over unreachable storages. This has the unfortunate side-effect of making it difficult to write finalisers, because the other objects to which an object ~Obj~ refers (and upon which its state may depend) may have already been finalised by the time ~Obj~'s finaliser is run. This is especially difficult when the compiler and collector are not cooperating, because what looks like separate memory objects to the collector may in fact be part of what is logically a single object at the source language level (and hence bugs may appear that the programmer has no way of preventing).

Yet another approach is to declare that finalisers shall not revive objects. With a stop-and-copy collector, this is not too hard to detect for debugging purposes; garbage is collected, finalisers are run, and the live objects are scanned for any references to just-finalised objects. Those found can be reported to the programmer. This can fail in a conservative collector, if finalisers write pointer-like bit patterns into non-pointer data.

In the case of Java, the approach taken was /to declare that finalisers are never run more than once per object/; if an object is revived in finalisation, that is fine, but its finaliser will not run a second time. It isn't clear if this is a matter of design, or merely an accident of the first implementation of the language, but it is in the specification now. Obviously, this encourages careful use of finalisation, in much the same way that driving without seat belts encourages careful driving.

One partial solution to this problem is to encourage people to use "the right tools for the job." Languages with GC often include control constructs for running finalisers at certain points in a program's execution. These can be used where timely, certain, finalisation is required. Finalisation associated with garbage collection can be used for those resources that are either abundant-but-not-infinite (like memory) or as a statistical backstop to reduce the loss of resources that are managed by hand (similar to the way in which garbage collection itself can be used as a backstop for manual deallocation).

### Free List
다 사용한 메모리 오브젝트를 따로 관리하다가 나중에 다시 사용하는 것은 매우 직관적인 개념이다. 다 쓴 메모리 블록을 단순히 리스트로 관리하기만 하면 된다. 그래서 초창기부터 가장 널리 쓰인 구현은 이런 다 쓴 오브젝트를 관리하는 Free List이다.


## 여러 알고리즘들
종류가 많다.

### Mark-Sweep Collection
 * 마킹: 가비지 찾기
 * 스위핑: 가비지 수집

#### Snapshot-at-the-beginning Invariant
마크 앤 스윕의 알고리즘 특성 상, **가비지 (즉 Unreachable Objects)의 수는 절대로 줄어들지 않는다**. 그래서 컬렉션 (정확히는 마킹) 을 시작하는 순간 현재 오브젝트들의 상태의 스냅샷(즉 주소 값들)을 복사해서 가지고 있으면서, 얘네들을 따라가서 가비지인지 여부를 확인한다. 이렇게 하면 **반드시 마킹 작업이 끝난다**는 것을 보장할 수 있는데, 컬렉션이 동작하는 도중에 힙에 오브젝트들이 계속 생기면, 이로 인해서 컬렉션이 늘어지거나 끝나지 않을 수 있기 때문이다. 그래서 보통은 이렇게 컬렉션이 시작하는 시점의 스냅샷만을 기준으로 GC가 동작한다.


### Mark-Sweep-Compact Collection
마크 앤 스윕만 하면 메모리 단편화가 발생함. 이걸 해결하기 위해서 스위핑 구간에 압축(컴팩트) 연산을 도입.

### Copying Collection
메모리를 두 덩어리로 나눈 다음 순차적으로 번갈아가면서 왔다갔다 하는거.

### Incremental Collection
responsiveness, 반응성이 중요.
전체 다 한꺼번에 하는게 아니라, 마킹이랑 스위핑 페이즈를 일단 나누고, 각 단계를 잘라서 (Slicing) 조금 씩 진행해서 (Incremental) 사용자 프로그램이 너무 긴 정지 시간 (Pause Time)을 겪지 않고 반응성이 좋도록 한다.

#### Write (Read) Barrier
Incremental을 도입하면 발생하는 문제를 해결하기 위해서 포인터 쓰기 연산에 도입되는 condition check. 컴파일러가 도와줘야 함. Barrier 라는 이름이 붙은 컬렉션은 incremental이 원조임.

앞의 세 가지 색깔 스킴을 다시 떠올려보자. 그러면 당연히 검은색에서 흰색으로 가는 포인터가 없어야 한다. 근데 incremental하게 하면, 컬렉터가 동작하다가 잠깐 멈추고 뮤테이터가 객체 상태를 변경할 때 이 불변식을 지켜야한다. 예를 들어 컬렉션 도중 A 가 검은색으로 칠해졌고 그 자식들이 회색으로 칠해졌다고 하자. 뮤테이터가 A -> C(검은색 -> 회색)로 포인터가 있던 걸 B -> D (둘 다 흰색)랑 교환한다고 하자. 이러면 A(검은색)은 D(흰색)를 가리키게 되고, B(흰색)은 C(회색)를 가리키게 된다. 그리고 D를 가리키는 유일한 포인터는 A가 된다. C는 B(흰색)에 의해 다시 Reachable 하게 되고, D는 A 외에는 포인터가 없는데 A가 이미 검은색(GC Reachability Traversal이 끝났음)이라서 절대 Reachable하지 않게 된다. 이러고 GC Marking이 끝나면 Sweeping 때 D는 흰색이라서 가비지로 간주되어 회수되는데 원래는 회수되면 안되는 애다. 그래서 이 invariant가 필요하다. 그래서 이걸 지키기 위해서 모든 포인터 쓰기 연산에 배리어를 도입한 것임.

A write barrier is a mechanism for *executing some memory management code* when a write to some object takes place (that object is then "behind the write barrier," or, informally, "write barrier-ed", or, sloppily, "write-protected"). It can take the form of in-lined code (if memory management is integral to the compiler), or a memory-protection fault which is handled by the memory management code. There are also "read barriers," the nature of which is obvious.

The roles a write barrier can play in GC are a little trickier to explain to a novice, but I'll give it a stab.

1. Consider a simple generational stop-and-collect collector. "Generational" means that data is partitioned into /old/ and /new/. This partition is useful to the GC for two reasons: (a) because data tends to die young, collecting just new data will probably free a lot of space, and (b) because pointers tend to point from new objects to old objects, and not vice versa, it is cheap to find all the pointers to new objects.
   *Property (b) is only true if you can tell when a pointer to a new object has been written into an old object*. Otherwise you have to scan all the old objects to find pointers to new objects, which loses one of the main advantages of generational GC. So you put the old data behind a write barrier, and record those writes. When you come to GC the new data, you know the /only pointers from old to new are those which you have recorded/.
2. Consider a tracing GC which is incremental or concurrent, i.e., the user's program or the 'mutator' can run before the GC is complete. Now there is an invariant: *black objects do not point to white objects*. If the mutator writes a white pointer into a black object, this invariant is broken and the GC can fail. There are two basic solutions: prevent the mutator from seeing white objects ("read barriers"), or prevent the mutator from writing white pointers into black objects ("write barriers"). *The write barrier solution puts the black objects behind a write barrier*. When a white-on-black write takes place, there are various fixes: incrementally grey the white object, re-grey the black object, etc.
   (Note) For a tracing collector, marking or copying, one conceptually colours the data white (not yet seen by the collector), black (alive and scanned by the collector), and grey (alive but not yet scanned by the collector). The collector proceeds by scanning grey objects for pointers to white pointers. The white objects found are turned grey, and the grey objects scanned are turned black. When there are no more grey objects, the collection is copmlete, and *all the white objects can be recycled*.

### Generational Collection
세대 가설 - 대부분의 데이터는 빨리 죽는다 (Die Young). 이로 인해서 말 그대로 여러 개의 힙을 운영하는 것이 가능해진다. 그래서 보통은 두 개의 힙을 운영한다.

#### Minor Heap
Youngest Heap, Bump Pointer Collection

#### Major Heap
Old Heap, Mark & Sweep Collection

#### Write (Read) Barrier
Generational을 도입하면 발생하는 문제를 해결하기 위해서 포인터 쓰기 연산에 도입되는 condition check. 컴파일러가 도와줘야 됨. Incremental에서 쓰이던 Barrier 기법이 그대로 적용되어서 같은 이름이 붙었고 요즘은 Generational에서 발생하는 문제가 더 커서 generational barrier가 좀더 유명함. 메이저 힙에서 마이너 힙으로 가는 포인터를 기록함.

### STW (Stop-The-World) Coordination
결국 트레이싱 컬렉션도 색깔을 칠하는 작업을 해야하기 때문에 오브젝트에 값을 써야하는데, 이로 인해 레퍼런스 카운팅과 마찬가지로 멀티 프로세스/쓰레드 환경에서 동기화가 필수적이다. 그래서 OCaml도 파이썬과 마찬가지로 GIL이 존재**했다**.

# OCaml 4.14의 경우
Generational + Incremental + Copying + Bump Pointer (Minor) / Mark-Sweep-Compact (Major) + STW.

## Memory Representation
박싱을 어떻게 하는지. 최하위 비트가 0인지 1인지를 가지고 어떤 값이 메모리 주소인지 아니면 해당 1비트를 제외한 나머지를 쉬프트해서 63비트짜리 정수값인지를 빠르게 판별함. 대부분의 프로그램은 정수를 많이 쓰니 말이 되는 접근.

주소값일 때는 다음과 같은 메모리 구조를 따름. 먼저 고정된 크기의 헤더를 까서 데이터의 타입이 무엇이고 크기는 얼마나 되는지를 알아낸 다음 실제 크기만큼 읽는다.

한 가지 추가 최적화로 부동소수점만으로 구성된 배열은 특수하게 함.

## Allocator Policy
### Next fit
### First fit
### Best fit

## Free List의 구현

## Space Overhead 튜닝 파라미터
JVM은 "너에게 할당된 메모리는 최대 이만큼이니 이 안에서 니가 최대한 열심히 해라" 이면, OCaml은 "너는 최대 이만큼의 메모리를 낭비하는 선에서 열심히 해라"임. 즉, JVM의 GC 파라미터는 구체적인 메모리 숫자 (예: 4GB)인 반면 OCaml은 퍼센티지(예: 30%)일 수 있음. JVM은 전통적인 프로덕션 환경, 즉 하나의 머신에서 하나의 프로그램이 독점적으로 돌아가는 환경을 가정하고 탄생한 언어라서 이게 말이 되긴 함. 근데 OCaml은 아님. 이건 애초에 연구 목적으로 탄생함. 그리고 성능이 생각보다 괜찮아서 다양한 곳에서 쓰이는데, 그러다보니 프로그램이 애초에 메모리를 얼마만큼 쓸지 알 수가 없음. 그래서 "요만큼만 낭비하세요"라는 접근이 말이 됨.

## Write Barrier 구현

## Major Collection 구현

## STW 구현

## Finaliser

OCaml의 finaliser는 `finalise.c` 파일에 구현되어 있으며, 주요 개념은 다음과 같습니다:

1. __두 개의 Finalisable Set__:

   - `finalisable_first`: Major GC cycle 동안 살아남은 객체들에 대한 finaliser. 객체가 unreachable이 되면 바로 실행 대상이 됩니다.
   - `finalisable_last`: 주로 C 라이브러리 리소스 해제 등에 사용되며, `Gc.finalise_last` 함수로 등록됩니다. 이들은 `finalisable_first`보다 나중에 처리됩니다.

2. __Finalising Set (`to_do`)__:

   - GC에 의해 unreachable로 판단된 객체들의 finaliser가 이 리스트로 이동합니다.
   - `to_do_hd`와 `to_do_tl` 포인터로 관리되는 연결 리스트입니다.

3. __등록__: `caml_final_register` (OCaml의 `Gc.finalise`) 또는 `caml_final_register_called_without_value` (OCaml의 `Gc.finalise_last`)를 통해 finaliser 함수와 값이 쌍으로 등록됩니다.

### GC와 Finaliser의 상호작용

1. __Mark Phase__:

   - `caml_final_update_mark_phase` (in `finalise.c`)가 호출됩니다.
   - `finalisable_first` 테이블을 검사하여 white (unreachable)인 값들을 찾아냅니다.
   - 찾아낸 값들은 `to_do` 리스트로 이동하고, 동시에 `caml_darken`을 통해 다시 mark phase로 들어갑니다 (liveness가 확정되기 전까지는 살아있을 수 있으므로). 이는 객체가 "revive"될 가능성을 고려한 것입니다.

2. __Clean Phase__:

   - `caml_final_update_clean_phase` (in `finalise.c`)가 호출됩니다.
   - `finalisable_last` 테이블을 검사하여 white인 값들을 찾아 `to_do` 리스트로 이동시킵니다.
   - 이때는 값을 darken하지 않습니다. 왜냐하면 이 값들은 `finalise_last`로 등록되었기 때문에 값 자체를 finaliser 함수에 전달하지 않고 `Val_unit`을 전달하기 때문입니다.

3. __Minor GC__:

   - `caml_final_update_minor_roots` (in `finalise.c`)가 호출됩니다.
   - Minor heap에 있는 값들 중 unreachable인 것들을 찾아 `to_do` 리스트로 이동시키거나, promoted된 값들은 major heap의 값으로 업데이트합니다.

4. __Finaliser 실행__:

   - `caml_final_do_calls_exn` (in `finalise.c`) 함수가 호출되어 `to_do` 리스트에 있는 finaliser들을 실행합니다.
   - 이 함수는 재진입 가능하도록 설계되어 있습니다.

### Java와의 비교 및 차이점

질문에서 언급한 글에서 다루는 문제들과 OCaml의 해결 방식을 비교해보면 다음과 같습니다:

1. __순환 참조 (Cycle) 문제__:

   - __문제__: Topological order로 finalisation을 하려 할 때 순환 참조가 있으면 순서를 정할 수 없습니다.
   - __OCaml__: OCaml은 topological order를 따르지 않습니다. 대신, GC의 mark phase를 활용하여 reachable한 객체들을 모두 mark하고, 남은 unmarked 객체들 (white)을 finalisation 대상으로 삼습니다. 이 과정 자체가 순환 참조가 있든 없든 모든 unreachable 객체를 찾아낼 수 있습니다. 순환 참조에 속하는 객체들은 모두 unreachable이므로 모두 `to_do` 리스트로 가게 됩니다. 실행 순서는 명확하지 않지만, 모두 실행은 됩니다.

2. __객체 부활 (Revival) 문제__:

   - __문제__: Finaliser 내에서 dead object를 다시 live object가 참조하게 만들면, 해당 객체는 다시 살아나야 합니다. 이 경우 finaliser가 두 번 실행되는 것을 막아야 합니다.

   - __OCaml__:

     - OCaml은 finaliser가 __한 번만 실행되도록 보&#xC7A5;__&#xD569;니다. 이는 Java의 명세와 유사합니다.
     - `finalisable_first`에 등록된 finaliser의 경우: `caml_final_update_mark_phase`에서 white 객체를 `to_do`로 옮기고, 동시에 `caml_darken`을 호출합니다. 만약 finaliser 내에서 객체가 부활되었다면, 그 객체는 다시 black으로 바뀌고, 다음 GC cycle까지는 살아남습니다. 현재 cycle에서는 더 이상 finaliser가 등록되어 있지 않으므로, 부활한 객체는 다음 cycle에서 unreachable이 되기 전까지는 다시는 finaliser가 실행되지 않습니다.
     - `finalisable_last`에 등록된 finaliser의 경우: `caml_final_update_clean_phase`에서 white 객체를 `to_do`로 옮길 때 값을 darken하지 않습니다. 이는 finaliser에 원래 값을 전달하지 않기로 한 약속을 지키기 위함일 뿐이지, revival을 막는 직접적인 메커니즘은 아닙니다. 하지만 이 값들은 `finalise_last`이므로 일반적으로 revival을 의도하지 않는 리소스 정리에 사용되고, 값 자체를 전달받지 않기 때문에 revival을 시도할 수도 없습니다. 그리고 이 경우도 `finalisable_first`와 마찬가지로 한 번 실행된 finaliser는 테이블에서 제거되어 재실행되지 않습니다.

3. __실행 순서 (Order) 문제__:

   - __문제__: Finaliser가 임의의 순서로 실행되면, finaliser 내에서 참조하는 다른 객체가 이미 finalised되었을 수 있어 문제가 발생합니다.

   - __OCaml__:

     - OCaml은 finaliser의 실행 순서를 __보장하지 않습니다__. `to_do` 리스트에 들어간 순서대로 실행되지만, 이 순서는 객체가 테이블에 등록된 순서나 GC가 객체를 찾은 순서 등에 따라 달라질 수 있습니다.
     - 이는 finaliser를 작성할 때 주의가 필요하다는 것을 의미합니다. 다른 객체에 의존하는 finaliser를 작성할 경우, 해당 객체가 먼저 finalised되었는지 확인하거나, 의존 관계를 고려하여 설계해야 합니다. 문서나 커뮤니티에서 권장하는 방식은 아닙니다.

4. __Write Barrier 문제__:

   - __문제__: Revival을 감지하기 위해 write barrier를 사용해야 할 수도 있지만, 이는 항상 가능한 것은 아닙니다.
   - __OCaml__: OCaml은 write barrier를 사용하여 revival을 실시간으로 감지하려 하지 않습니다. 대신, GC cycle 단위로 처리합니다. `caml_darken`을 호출하여 부활 가능성을 mark phase에 반영하고, 한 번 실행된 finaliser는 테이블에서 완전히 제거함으로써 두 번 실행되는 것을 방지합니다.

### 결론

OCaml 4.14.2는 finaliser와 관련된 여러 문제를 다음과 같은 방식으로 해결하고 있습니다:

1. __한 번만 실행__: Java와 마찬가지로, OCaml도 각 객체의 finaliser가 __최대 한 번만 실행되도록__ 보장합니다. 이는 `finalise.c`의 구현, 특히 `finalisable_first`/`finalisable_last` 테이블에서 실행 대상 객체를 `to_do` 리스트로 이동시키고 원래 테이블에서는 제거하는 로직을 통해 달성됩니다.
2. __GC 통합__: Finalisation 과정이 Major GC의 Mark/Clean phase와 깊이 통합되어 있습니다. 이는 GC 알고리즘의 정확성을 이용하여 (순환 참조든 직선 구조든) 모든 unreachable 객체를 효과적으로 찾아냅니다.
3. __순서 비보장__: 실행 순서는 보장하지 않으며, 이는 프로그래머가 finaliser를 작성할 때 주의해야 할 점으로 남겨둡니다.
4. __Revival 처리__: 부활 문제는 GC cycle 단위의 처리와 한 번 실행 보장 정책을 통해 해결합니다. 실시간 write barrier 감시는 하지 않습니다.

전반적으로, OCaml은 Java와 유사하게 "finaliser는 한 번만 실행된다"는 강력한 보장을 제공하면서도, 실행 순서에 대한 보장은 하지 않는 pragmatic한 접근을 취하고 있습니다. 이는 GC 구현의 복잡성을 줄이고, 동시에 프로그래머에게 일정 부분 책임을 요구하는 설계입니다.


# 재밌는 사실들
## Duality
사실 레퍼런스 카운팅이랑 트레이싱 컬렉션은 수학적으로 듀얼이다!

## 비용
여전히 풀리지 않은 문제다. 가비지 컬렉션 자체의 비용을 측정하는 것은 엄청나게 어렵다. 당장 같은 언어로 구현된 서로 다른 알고리즘을 비교하는 것도 어려운 문제인데. 수동으로 메모리를 관리하는 언어와 가비지 컬렉션 언어를 비교하는 것은 너무나도 방해하는 요소들 (Confounding Factors)가 많다. 당장 C언어와 OCaml을 비교한다고 치면,
 * 메모리 레이아웃: 논리적으로 같은 데이터 구조를 표현하더라도, 언어마다 데이터를 표현하는 메모리 레이아웃이 다르다. C에서는 64비트 정수가 곧바로 표현되지만 OCaml에서는 박싱된 정수가 기본으로 쓰이고 (Boxed Integer), 구조체나 struct로 들어가면 차이는 더욱 심각해진다. 이로 인해서 캐시 지역성에서 차이가 나게 되어서 성능 차이를 가린다.
 * 배열 바운드 체크: OCaml은 모든 배열 연산에 기본적으로 바운드 체크를 한다 (진짜인가?)
 * 함수 호출: C는 표준적인 함수 호출 컨벤션을 따르는 반면, 함수형 언어인 OCaml에서는 클로저가 오버헤드가 있다.
 * 컴파일러 최적화: 수십년간 수많은 엔지니어와 연구자들이 최적화한 GCC/Clang에 비해서 OCaml의 최적화는 부족한 부분이 있을 수 있다.
 * Write Barrier 오버헤드: OCaml의 Generational GC를 위해서 Write Barrier는 필수인데, 이 오버헤드는 GC 시간 측정에 포함되지 않는다.
 * 메모리 할당자: OCaml은 GC의 할당자를 쓸 수 밖에 없지만, C에서는 다양하게 최적화된 할당자들이 많다. tcmalloc, jemalloc 등. 이 중에 어떤 걸 써야 공정한 비교일까?
 * 가비지 컬렉션 자체의 튜닝 파라미터: 가장 유명한 GC 언어인 Java의 경우, "너한테 할당된 메모리 용량은 최대 이만큼임" 정도의 튜닝만이 가능하다. 그래서 메모리를 약간 낭비하면서 속도를 가져가려는 경향이 있다고 한다. 반면 OCaml의 경우는 "실제로 써야하는 메모리보다 최대 이만큼 정도만 낭비하도록 하세요" 느낌의 튜닝이 가능하고, 이를 Space Overhead 라고 한다. 즉, 실제로 메모리 할당이 100GB를 했고, 20%의 공간 오버헤드를 파라미터로 갖고 있다면, 최대 120GB 만큼의 메모리만 사용하도록 GC가 열심히 일할 것이다.

그러니까 공정한 비교라는 것은 애초에 불가능한 것일지도 모른다.

---

글을 적는데 참고한 것들.
 - [Uniprocessor Garbage Collection Techniques](https://www.cs.cmu.edu/~fp/courses/15411-f08/misc/wilson94-gc.pdf) by Paul R. Wilson (CMU)
 - [A Unified Theory of Garbage Collection](https://web.eecs.umich.edu/~weimerw/2008-415/reading/bacon-garbage.pdf) by David F. Bacon et. al (IBM Watson)
 - [MemFix: Static Analysis-Based Repair of Memory Deallocation Errors for C](https://prl.korea.ac.kr/papers/fse18.pdf)
 - [Memory Management](https://signalsandthreads.com/memory-management/) with Stephen Dolan (Jane Street)
 - [OCaml 4.14.2](https://github.com/ocaml/ocaml/tree/4.14) Source Code
 - [The Saga of Multicore OCaml](https://youtu.be/XGGSPpk1IB0)
