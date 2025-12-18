---
layout: post
published: true
tag: [dev, essay]
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
"애초에 가비지 컬렉션이 왜 필요함? 처음부터 메모리 이슈 없게 잘 짜면 되는 거 아님?" 이라고 생각하기 쉽다. 나도 그랬다. 하지만, 꼭 가비지 컬렉션이라는 방법이 아니더라도, 메모리 관리를 위한 다양한 방법론이 여전히 연구 되고 있는 데에는 다 이유가 있다.

## 과거와 현재

먼저 역사적인 배경을 한번 살펴보자. 최초의 가비지 컬렉션이 LISP 언어에 도입된 이유 중 하나로, 당시 ALGOL과 같은 프로그래밍 언어에서 댕글링 포인터 문제, 그러니까 어떤 이유에서든 쓰던 메모리를 이미 해제했는데 그걸 모른채로 메모리 주소를 계속 갖고 있다가 나중에 잘못 사용해버려서 결국 Use After Free 버그로 나타나는 문제가 심각한 이슈로 떠올랐다는 것이 있다. 그 당시 프로그래머라면 정말 똑똑한 소수의 선택된 사람들일텐데, 그런 친구들에게도 수동으로 메모리를 관리하는 일은 쉽지 않았던 것이다.[^1]

[^1]: 물론 최초의 가비지 컬렉션은 여러가지 한계로 인해 "너무 느리다"는 비판을 받긴 했지만, 이것이 씨앗이 되어서 지금은 많은 언어에 표준적인 기능으로 자리잡았다.

**근데 이 문제는 현재도 해결되지 않았다.** 오히려 인터넷이 발전하면서 더 심각해졌다. Use After Free 버그는 이제 프로그램이 죽는 데서 그치지 않고 더 큰 문제를 만든다. 인터넷이 발전하면서 정말 많은 것들이 가능해졌지만, 그와 동시에 프로그램의 보안 취약점이 더 이상 단순한 문제가 아니게 되었다. [마이크로소프트의 한 조사](https://www.microsoft.com/en-us/msrc/blog/2019/07/we-need-a-safer-systems-programming-language)에 따르면 매년 CVE (공개적으로 알려진 보안 취약점에 아이디를 붙이는 시스템) 의 약 70%가 메모리 안전정 문제라고 한다. [구글에서도 비슷한 결과](https://www.zdnet.com/article/chrome-70-of-all-security-bugs-are-memory-safety-issues/)를 발표한 적이 있는데, 크롬의 심각한 보안 관련 버그 중 70%가 메모리 관련 오류, 그 중 절반이 Use After Free였다고 한다.

1960년대에 발견된 문제가 2020년대에도 여전히 보안 취약점의 대다수를 차지한다는 건 수동 메모리 관리가 정말로 어렵다는 걸 말해준다. 게다가 이 단순해 보이는 메모리 오류가 프로그램의 보안에 구멍을 뚫리게 하고 이로 인해 정말로 상상도 못할 피해를 끼칠 수도 있게 된 것이다.

## 문제의 난이도

"메모리 이슈 없게 잘 짜면 되는 거 아님?"이 얼마나 어려운지를 보여주는 또 다른 명확한 근거는 바로 이 문제 자체의 본질적인 난이도이다. 메모리 오류의 대부분은 결국 커널로부터 힙 메모리를 할당 받아서 (`malloc`) 쓴 다음에 이걸 적절한 타이밍에 돌려줘야 (`free`) 하는 이 *타이밍*이 어긋나서 발생하는 것이다. 메모리를 할당하고 돌려주는 시점은 정확하게 알아낼 수 없다. 즉, "여기서 할당되어서 사용되던 메모리가 코드의 여기에서 딱 사용이 끝날테니 여기다가 `free`를 넣으면 되겠다" 라는 분석이 이론적으로 **불가능**하다. 좀더 구체적으로는 코드만 봐서는 할당된 메모리의 수명을 알아내는 알고리즘은 만들 수 없다 (Undecidable).[^2] 그렇다고 프로그램이 끝나는 시점에 한꺼번에 메모리를 돌려줘버리면 애초에 메모리를 관리하려는 의미가 없지.

[^2]: 그래서 Rust의 경우 언어의 표현력을 제한해서 이 문제를 결정 가능한 수준으로 축소해서 풀고, 컴파일러가 추론이 불가능하면 프로그래머에게 명시적인 라이프타임 어노테이션을 떠맡긴다.

그럼 문제를 조금 더 쉽게 줄여서, "이 메모리는 크기는 이 정도 되고 수명은 이 정도 된다" 라는 정보가 미리 알려져 있을 때 얘네들을 잘 배치해서 메모리 사용량을 최소화 하도록 하는 *동적 스토리지 할당 (Dynamic Storage Allocation, DSA)* 문제를 생각해볼 수 있다. 근데 이 문제는 NP-Complete 임이 증명되어 있다. 즉, 메모리를 잘 배치해서 최소한의 메모리만 사용하도록 계산하는 알고리즘이 있긴 있는데, 언제 끝날지 모른다. 이는 메모리의 생명주기가 (Lifetime) "이미 알려져 있는" 경우에도 최적의 배치를 찾는 것이 어렵다는 말이다. 아무튼 간에 메모리를 할당하고 돌려주는 타이밍을 맞추는 문제가 엄청나게 어렵다는 뜻이다.


## 인지적 부하

내가 더 중요하게 생각하는 점 중 하나는 바로 인지적인 부하이다 (Cognitive Load). 이제 현대의 복잡한 대규모 소프트웨어를 혼자서만 개발하는 것은 굉장히 어렵다. 설령 작은 규모를 혼자서 만들더라도 현재의 나와 미래의 나는 다른 사람이다. **코드는 쓰이는 것보다 훨씬 더 많이 읽힌다**. 관련해서 많은 격언들이 있다. 엉클 밥의 "읽기와 쓰이게 소요되는 시간의 비율은 10:1을 훨씬 상회한다" 라던지, 귀도 반 로썸의 "코드는 쓰이는 것보다 더 자주 읽힌다" 라던지. 그래서 어떤 코드 베이스를 이해하는 작업은 어렵다. 어떤 코드 한 줄을 이해하려고 한다고 하자. 만약 지금 보고 있는 코드가 속한 함수나 파일만이 아니라, 코드 베이스 전체, 심지어는 프로젝트가 사용하고 있는 라이브러리를 다 따라가서 연관된 모든 것들을 다 고려해야 한다면 (Global Reasoning) 결코 쉽지 않을 것이다. 그런데 만약 따라가서 살펴봐야 할 코드가 적은 지역적인 추론만이 필요하다면 (Local Reasoning), 이 작업은 한결 수월해질 수 있다.

진정한 의미의 "모듈화된 프로그래밍 (Modular Programming)"에서 가비지 컬렉션은 필수적이다. 모듈 사이에 의존성이 어쩔 수 없이 생길 수는 있다. 하지만 모듈이 동적으로 메모리를 할당하고 사용해야만 할 때, 이 메모리의 소유권 (Ownership) 분쟁이 발생하게 된다. 특히, 모듈이 엮인 객체의 생명주기는 **전역적인 속성**이다. 예를 들어, 모듈 A가 할당하는 어떤 객체를 모듈 B와 C가 공유하게 되면, 객체가 언제 할당되고 해제될지를 알아내려면 이 세 모듈을 **모두** 추적해야만 한다. 이렇게 모듈의 사용 방법 뿐만 아니라 모듈과 엮인 메모리도 고려해야 한다면, 원래는 지역적으로 이해 가능하고 유연하게 조합하기 위해서 만들어진 모듈식 프로그래밍인데도 불구하고, 전역적으로 모듈이 사용하는 메모리를 관리하고 생존 여부를 추적해야 하기 때문에 추상화가 어그러뜨려지고 이해에 방해를 받게 된다. 게다가 이런 관리 작업을 추가로 구현하다 보면 런타임에서 비용도 상당할 수 있고, 멀티 쓰레드 어플리케이션이면 동기화도 고려해야 한다. 아무튼 간에 복잡해진다.

결국 언어 설계는 안전성, 표현력, 성능, 사용성 사이의 트레이드오프를 고려해야 한다. 가비지 컬렉션은 약간의 성능을 희생하면서 안전성, 표현력, 사용성을 모두 챙겨갈 수 있는 좋은 선택지이다.

# 추상화
그럼 이제 가비지 컬렉션에 대해서 하나씩 알아보자.

먼저 존 매커시의 설명을 다시 풀어 쓰면 다음과 같다: "프로그램의 어디에서도 사용하지 않는 메모리는 가비지로 간주하고 따로 모아뒀다가 나중에 재활용한다." 이로부터 가비지 컬렉션을 아주 추상적인 두 단계로 나눌 수 있다.
 1. **가비지 찾기 (Garbage Detection)**: 살아있는 객체(Live Object, Reachable Object)와 쓰이지 않는 가비지(Dead Object, Unreachable Object, Garbage)를 어떤 식으로든 구별한다.
 2. **가비지 수집 (Garbage Collection)**: 가비지 객체의 메모리를 수집한다. 곧바로 커널에게 돌려줄 수도 있고, 아니면 따로 모아놨다가 재활용할 수도 있다.

실제로 이 두 단계는 완전히 구분되지 않은 채로 얽혀 있을 수 있고, 특히 수집 방법은 찾는 방법에 크게 의존하는 경우가 많다.

## 몇 가지 기본적인 개념들

### 컬렉터와 뮤테이터
흥미롭게도 가비지 컬렉션 연구자들은 사용자 프로그램을 "뮤테이터(Mutator)"라고 부르는데, 왜냐하면 사용자 프로그램이 메모리의 상태를 계속해서 바꾸기 (mutate) 때문이다. 철저하게 가비지 컬렉션 입장에서 이름 지은 거라서 웃겼다. 그리고 가비지 컬렉션이 탑재된 언어에서 가비지 컬렉션을 담당하는 컴포넌트를 가비지 컬렉터, 혹은 그냥 컬렉터(Collector)라고도 부른다.

### Boxing
레퍼런스 카운팅이 참조 횟수를 세어야해서 객체마다 박싱이 필요하여 오버헤드가 발생한다고 했는데, 사실 이건 트레이싱도 마찬가지다. 가비지의 탐지와 수집 두 단계를 명시적으로 구분하였고, 가비지 탐지 단계에서 "얘는 가비지임"과 "얘는 가비지 아님 (Live Object)"을 기록하려면, 해시 테이블에 객체마다 메타데이터를 기록하던지, 아니면 객체를 직접 박싱해서 기록하던지 둘 중 하나밖에 없다. 그래도 수많은 연구를 통해 트레이싱 컬렉션만을 위한 효율적인 박싱 방법이 개발되어왔다. 예를 들면 [현대의 가상 메모리 시스템의 특징](../virtual-memory#%EC%A3%BC%EC%86%8C%EB%8A%94-%ED%95%AD%EC%83%81-%EC%A7%9D%EC%88%98)을 이용해서 모든 메모리 주소가 짝수임을 이용하여 최하위 비트가 0인지 1인지에 따라서 주소값을 따라 박싱된 값인지 아니면 어떤 원시적인 값인지를 판별할 수 있는데, 이걸 이용하는 언어들이 꽤 있다.

### 루트 집합
프로그램이 실행 중인 어떤 시점에서, 실행 중인 프로그램의 부분이 바로 사용할 수 있는 데이터를 **루트 집합(Root Set)**이라고 한다. "바로 사용할 수 있다"는 뜻은 어떤 포인터를 따라가지 않고도 곧바로 접근 가능하다는 뜻이다. 예를 들면, 실행 중인 함수의 로컬 변수들이나 글로벌 변수들, 정적인 모듈들 등이 있다. 트레이싱 컬렉션은 이 루트 집합으로부터 시작해서 닿을 수 있는 모든 객체들을 탐색하는 일종의 그래프 탐색이라고 이해할 수 있다.

트레이싱 컬렉션은 이 루트 집합이 사용 중인 데이터(객체)들은 가비지가 아니다는 사실을 근거로 동작한다.

### 세 가지 색깔 (Tri Colour)
많은 트레이싱 컬렉션은 저마다의 방식으로 객체의 상태를 구분하는데, 가장 널리 쓰이는 방법 중 하나는 아래의 세 가지 색깔을 이용하는 방식이다.

 * 흰색: 흰색은 가비지 탐지의 시작과 끝, 그리고 가비지 수집 단계에서 그 의미가 조금씩 다르다.
   * 가비지 탐지 단계의 시작에서: 모든 오브젝트의 초기 상태를 나타낸다. 컬렉터는 루트 집합으로부터 닿을 수 있는 흰색 객체들을 하나씩 보면서 색깔을 칠해나간다.
   * 가비지 탐지 단계가 완료되었을 때: 가비지 탐지 단계가 완료되었는데도 여전히 흰색인 객체들은 루트 집합으로부터 닿을 수 없는 객체들 **(Unreachable Objects)**, 즉 **가비지**를 뜻한다.
   * 가비지 수집 단계: **가비지 수집 대상**이다. 가비지 수집 단계에서 여전히 흰색인 객체들의 메모리를 프리 리스트에 매달아뒀다가 나중에 할당에 재사용한다.
 * 회색: 회색은 가비지 탐지 단계에서만 일시적으로 나타나는 상태를 표현하기 위한 색깔이다. 어떤 객체가 루트 집합으로부터 닿긴 했는데 아직 그 자식들(포인터를 따라갈 수 있는 객체들)까지는 탐색되지 않은 상태를 뜻한다.
 * 검은색: 루트 집합으로부터 닿을 수 있는 객체들 (**Reachable Objects**), 즉 "살아있는 객체들 (Live Object)"을 뜻한다. 얘네들은 아직 프로그램이 사용하고 있는 객체일 수 있기 때문에 가비지 수집 단계에서 살려둔다. 이때, 가비지 수집 단계에서는 검은색 객체들의 색깔을 다시 뒤집어서 흰색(초기 상태)으로 돌려둔다.

이걸 바탕으로 가비지 컬렉션 알고리즘은 닿을 수 있는 객체들로 구성된 그래프를 탐색하면서 색깔을 칠하는 것으로 이해할 수 있다. 즉, 가비지 컬렉션이 동작하면, 제일 처음에는 모든 노드(객체)들이 흰색이고 포인터를 따라 닿을 수 있으면 엣지가 있고 그렇지 않으면 엣지가 없는 모습이다. 이후 노드를 하나씩 방문하면서 회색으로 칠해지고, 자식 노드로 넘어갈 때 부모 노드는 검은색으로 칠해지면서 자식 노드는 회색이 된다. 즉, 흰색 -> 회색 -> 검은색의 물결이 진행되며, 모든 노드는 회색을 기준으로 한쪽은 흰색 다른 한쪽은 검은색인 그래프 탐색을 상상해볼 수 있다. 모든 엣지들을 다 탐색해서 색깔 칠하기가 끝나고 나면 남아있는 흰색 노드들은 수집되어 나중에 재활용되고 검은 노드들은 이번 컬렉션을 살아 남아 다음 컬렉션을 위해 다시 흰색으로 돌아간다.

### Free List
다 사용한 메모리 오브젝트를 따로 관리하다가 나중에 다시 사용하는 것은 매우 직관적인 개념이다. 다 쓴 메모리 블록을 단순히 리스트로 관리하기만 하면 된다. 그래서 초창기부터 가장 널리 쓰인 구현은 이런 다 쓴 오브젝트를 관리하는 Free List이다.

---

가비지 컬렉션 알고리즘은 크게 두 갈래로 나뉜다. 각 객체의 참조 횟수를 추적해서 0이 되면 즉시 수집하는 **레퍼런스 카운팅(Reference Counting)**과, 주기적으로 지금 쓰고 있는 객체와 안쓰는 가비지를 추적해서 가비지만을 수집하는 **트레이싱 컬렉션(Tracing Collection)**이 있다.

# 레퍼런스 카운팅
레퍼런스 카운팅은 두 단계 추상화를 다음과 같이 구현한다.
 1. 가비지 찾기: 각 객체의 참조 횟수를 유지하면서 프로그램이 실행되는 동안 객체를 참조하면 횟수를 늘리고 다 쓰면 줄이다가 0이되는 즉시 가비지로 판단한다.
 2. 가비지 수집: 참조 횟수가 0이 되는 즉시 관련된 객체의 모든 메모리를 수집한다.

이 방식의 특징은 위의 1, 2가 동시에 일어난다는 점이다.

레퍼런스 카운팅은 여러가지 장점과 단점이 있다. 장점으로는 메모리(객체)를 다 쓴 *즉시* 수집하기 때문에 객체의 수명이 명확해서 메모리를 되도록 필요한 만큼만 사용하는 편이고, 종료 처리도 (Finalise) 예측한 대로 동작한다. 그리고 통상적으로 메모리 관리의 응답 시간이 짧아서 응답성이 좋은 편이라 주로 실시간 시스템에서 채택된다. 그리고 생각보다 구현도 간단하다...고 하는데, CPython 구현 코드에서 레퍼런스 카운터를 [늘리거나](https://github.com/search?q=repo%3Apython%2Fcpython%20py_incref&type=code) [줄이는](https://github.com/search?q=repo%3Apython%2Fcpython+py_decref&type=code) 코드를 검색하면 엄청 많은 곳에서 발견되어서, 그렇게 쉬울 거라는 생각은 들지 않는다.

그런데 실제로 주변을 둘러보면 레퍼런스 카운팅**만** 가비지 컬렉션으로 도입한 언어나 프로그램은 거의 없다. 그 이유는 다음과 같은 여러 근본적인 한계 때문이다.

## 정확성의 한계

가장 큰 한계는 바로 그 유명한 순환 참조(Circular Reference) 이슈로, 두 객체가 서로 참조해버리면 이 객체(들)을 사용하던 곳이 일을 다하고 소멸되어도 여전히 참조 횟수가 1 이상이라서 절대로 수집되지 않는다는 것이다 (Memory Leak). 이런 데이터가 얼마나 많겠냐 싶겠지만 실제로 생각보다 많다. 예를 들면 LRU 캐시에 사용되는 더블 링크드 리스트의 구현이나, 혹은 편의를 위해 부모 노드로 가는 포인터를 추가한 트리 노드 등은 꽤 자주 쓰인다.

즉, 문제는 레퍼런스 카운팅이 가비지를 찾는 방식이 그 한계로 인해서 보수적인 근사값(Conservative Approximation)만을 판단한다는 점이다. 그러니까, 어떤 객체의 참조 횟수가 0이면 무조건 가비지이지만, 그 역은 참이 아닐 수도 있다.

## 성능 오버헤드

또, 생각보다 오버헤드가 크다는 점이 있다. 일단 모든 객체에 "레퍼런스"라는 걸 도입해야 하는데, 말 그대로 **모든** 객체, 즉 언어가 제공하는 원시 데이터 타입 외에 사용자가 정의하는 것까지 포함해야 하기 때문에, 객체를 표현하는데 제약이 생긴다. 그래서 보통 레퍼런스를 포함한 메타데이터 정보를 담는 일종의 박스 객체를 만들고 그 안에 메모리 공간을 동적 할당해서 실제 데이터인 원시 타입이나 사용자 정의 타입을 담는데, 이걸 박싱된 객체 (Boxed Object) 라고 한다.

박싱된 객체는 보통 정해진 형태를 따라 힙에 할당된다. 이로 인해 모든 데이터는 단순한 값이 아니라 포인터 값이 되고, 이 포인터를 따라 가서 박싱된 객체의 헤더를 살펴본 후에 진짜 데이터를 참조하게 되어서 [간접적인 메모리 오버헤드](../virtual-memory)가 발생한다. 게다가, 참조 "횟수"를 세기 위해서는 헤더에 적어도 정수를 담아야 하는데, 프로그램이 실행되면서 최대 몇 번의 참조가 이뤄질지는 알 수 없기 때문에, 적당한 크기의 정수를 선택하는 것도 어려운 문제다.

객체에 접근하는 모든 작업에 추가적인 연산을 하는 것도 오버헤드이다. 어떤 객체가 담고있던 객체가 다른 객체로 바뀌면 한 객체의 레퍼런스는 늘이고 한 객체는 줄인 다음 0이 되었는지 확인해야 한다. 그러니까 **두 객체**의 레퍼런스를 업데이트 해야 한다! 그래서 프로그램의 작업량 자체가 크면 여기에 비례해서 오버헤드도 늘어난다. 게다가 어떤 커다란 객체의 카운트가 0이 되어서 그 객체를 따라 연결된 수많은 객체들이 모두 다 해제되어야 하는 상황이 오게 되면, 일관되고 예측 가능한 성능이 깨진다는 점도 무시할 수 없다.

## 메모리 재사용의 어려움

의외로 메모리 재사용이 어렵다는 점도 꼽을 수 있다. 레퍼런스가 0이 된 객체의 메모리를 즉각 회수하지 않고 프리 리스트 (Free List) 같은 곳에 잠깐 관리했다가 나중에 재사용하려고 한다면, 이 커다란 객체의 해제 시점에서 모든 연결된 객체들을 다 따라가서 이것들을 일일이 다 프리 리스트에다가 넣어야 하고, 나중에 객체가 생성될 때 이 프리 리스트에서 지금 필요한 적당한 크기의 메모리를 가져와서 초기화를 해줘야 하는 등의 피할 수 없는 오버헤드가 **즉시** 발생한다. 게다가 프리 리스트를 도입해버리면 사실상 트레이싱 컬렉터의 특징을 갖게 되는데, 이러면 원래 장점이었던 응답성이라던지 예측 가능한 종료 처리도 잃어버리게 된다.

## 병렬 처리

개인적으로 겪었던 단점 중 하나는 바로 **객체를 읽는 모든 연산이 쓰기 연산이 되어버린다**는 것이었다. 이로 인해서 데이터를 단순히 읽기만 하는 것이 원천적으로 불가능하다. 예를 들어 커다란 데이터 덩어리를 여러 프로세스 사이에 읽기만 하는 목적으로 공유하는 경우, 커널이 제공하는 최적화 중 하나인 [쓰기 시 복사(Copy-on-Write)](../virtual-memory#cow-copy-on-write)를 적용하는 것이 불가능해져서 예상했던 것보다 엄청나게 많은 메모리를 잡아먹게 된다. 그래서 병렬 처리가 불가능했던 적이 있다. 이럴 때는 데이터를 곧바로 로딩하기 보다는 다른 라이브러리를 이용해서 읽기만 할 데이터를 공유 메모리에 올리거나 하는 방식으로 우회해야 한다.

최적화를 못받는다는 점 외에도 "읽기가 곧 쓰기"가 되는 특성으로 인해서 공유 메모리 병렬 처리 (Shared Memory Parallelism), 다시 말해서 멀티 쓰레드 환경에서의 런타임의 구현이 어려워진다. 여러 개의 쓰레드가 어떤 공유된 객체를 "읽기"만 해도 카운터를 "쓰게" 되는데, 이로 인해 발생하는 경쟁 상태를 피하기 위해서는 반드시 동기화가 필요하다. 그래서 이를 간단하게 하기 위해서 파이썬은 GIL(Global Interpreter Lock)을 도입하기도 했다.

## 레퍼런스 카운팅의 현재

이러한 한계들로 인해서 현대에는 레퍼런스 카운팅만을 도입한 언어는 잘 없다. 보통은 다음 둘 중 하나를 택한다.[^3]
 * 하이브리드 접근: 레퍼런스 카운팅을 기본으로 하되, 순환 참조를 피하기 위해서 보조 트레이싱 컬렉션을 도입한다. 예를 들면 파이썬과 스위프트가 있다.
 * 제약된 레퍼런스 카운팅: 순환 참조를 방지하도록 소유권 규칙을 강제한다. Rust의 `Rc<T>`가 있다.

[^3]: 하지만 레퍼런스 카운팅 "알고리즘" 자체는 유용하게 널리 쓰이는 편이다. 예를 들면, C++의 스마트 포인터나 유니크 포인터가 그러하고, 혹은 정말로 이런 식으로 밖에 관리할 수 없는 외부 리소스들, 예를 들어 파일 식별자에 대해서 자동으로 `open`/`close` 쌍을 호출할 때 필요하다.

그리고 사실 레퍼런스 카운팅은 생각보다 최적화할 여지가 많지 않아서, 가비지 컬렉션과 관련된 많은 연구는 주로 아래에 설명할 트레이싱 컬렉션 위에서 진행되는 편이다.

# Tracing Collection
트레이싱 컬렉션은 말 그대로 "따라가서" 가비지를 수집한다. 이 방법은 앞에서 설명한 가비지 컬렉션 추상화의 두 단계, 즉 (1) 가비지를 추적하고 (2) 가비지를 수집하는 것을 정직하게 구분한다. 어떻게 가비지를 추적하는지, 그리고 어떤 식으로 가비지를 수집하는지 다양한 연구와 방법들이 나와있는데, 그전에 몇 가지 기본적인 개념을 정리하고 가면 좋다.

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


# 고급 기능들
이렇게 가비지 컬렉션은 자동으로 객체의 메모리를 할당하고, 가비지 여부를 탐지하고, 메모리를 수집해뒀다가 재사용하게 해주지만, 가끔은 컬렉터의 감시를 벗어나 프로그래머가 더 미세 조정을 할 수 있게 하는 고급 기능들도 필요하다. 레퍼런스 카운팅이든 트레이싱 컬렉션이든 상관없이 보통은 아래와 같은 고급 기능들이 있다.

## 약한 포인터 (Weak Pointer)
가비지 컬렉터가 장착된 언어는 약한 포인터라고 불리는 기능이 제공되는 경우가 많다. 약한 포인터, 또는 Weak Pointer는 컬렉터와 상호작용하는 특수한 포인터이다. 약한 포인터가 가리키는 객체는 컬렉터가 메모리를 언제든지 회수할 수 있다. 즉, 이름 그대로 힘이 약해서, 컬렉터가 메모리를 회수하는 걸 막지 못한다 (...).

어떤 객체를 쓰고 있는 게 약한 포인터 뿐이라면 이 객체는 언제든지 사라질 수 있다. 그래서 약한 포인터가 담고 있는 데이터에 접근할 때에는 반드시 아직 살아있는지를 검사해야 한다. 한마디로 객체의 상태를 관찰하기만 할 뿐, 그 객체의 생명주기에는 영향을 미치지 않는다.

그럼 이걸 어디다 쓸 수 있을까?

섹션이 조금 애매하긴 한데, 약한 포인터는 원래 레퍼런스 카운팅의 순환 참조 문제를 부분적으로 해결하기 위한 도구이다. 즉, 두 객체 A와 B가 있을 때 A -> B, B -> A 방향으로 순환 참조가 일어날 수 있는데, 이때 B -> A를 약한 포인터에 의한 참조로 바꾸면 올바르게 메모리를 회수할 수 있게 된다. 하지만 이건 프로그래머가 미리 순환 참조를 머릿속에 그려서 대응해야 한다.

트레이싱 컬렉션에서는 주로 캐싱 및 메모이제이션에 활용된다. 캐싱을 위해서 잠깐 동안만 가지고 있는 데이터는, 그 데이터를 실제 참조하는 지역적인 부분에서만 쓰이는 동안에만 살아있으면 된다. 이후에는 캐시니까 언제든지 컬렉터가 가져가도 문제 없다. 사실 효율적인 캐싱을 생각해보면 약한 포인터가 너무 약해서 너무 빠르게 회수되어 버리면 오히려 효율적이지 못해서, 캐싱을 위해서는 조금 덜 약한(?) 포인터가 도입되기도 한다. 예를 들면 자바에서는 진짜 약한 포인터인 `WeakReference`가 있긴 하지만, 캐싱을 구현할 때에는 좀 덜 약한 포인터인 `SoftReference`를 쓴다고 한다.

## Ephemeron

약한 포인터를 좀더 일반화한 개념이 바로 Ephemeron이다. 에피메론? 아니면 발음 기호대로 읽으면 이페머른? 정도 되는 것 같은데 뜻은 수명이 아주 짧은 것을 뜻한다. 그래서 이걸 뭐라고 번역해야 할지 모르겠다. 그냥 여기서는 끔찍한 혼종으로 이페메론 정도로 하겠다.

약한 포인터의 일반화된 개념이 이페메론이라고 할 수 있다. 이페메론은 논리적으로는 키 값 쌍을 담은 일종의 해시 테이블 혹은 딕셔너리인데 키는 약한 포인터이고 값은 강한 포인터이다. 그리고 이 딕셔너리 자체는 강한 포인터이다. 그래서

GC의 두 개의 연결된 문제를 해결하기 위해 도입된 데이터 구조임. 하나는 이 객체가 수집되기 직전에 알림을 줌. 다른 하나는 어떤 객체를 참조하지 않고도 그 객체와 데이터를 연결할 수 있도록 해서 객체가 가비지 컬렉션되는 것을 방지함 (이게 대체 무슨말?). 논리적으론 키-값 쌍이고 키는 에피메론이 보호하는 객체로 수집될 때 시스템에 알림. 값은 임의의 데이터이고 비어있을 수 있음. GC에 의해 특별하게 처리됨.

## Finaliser
레퍼런스 카운팅과 달리 객체가 수집되는 시점을 정확하게 알 수 없기 때문에 Finaliser 구현이 까다로움. (좀더 조사 필요)

Finalisation, or destruction, is problematic. It is generally useful, but people disagree on how certain and timely it should be. The difficulty here is that in practice, no garbage collector provides an absolute guarantee that it will detect every single instance of unreachable storage in a bounded amount of time. Some GC designs deferred collection of regions of memory likely to contain mostly live memory, some can be "fooled" by bit patterns stored in integers, and in some cases artefacts of compilation (such as register use and calling conventions) will keep memory allocated long after it "should be" recycled. Reference counting is not immune to this problem; overflowed reference counts and cycles can both prevent collection, and some reference counting algorithms defer collection.

Yet another problem with finalisation is the difficulty of defining a proper order for finalisation. There are numerous problems, none with a clean solution.

For instance, it makes a certain amount of sense to finalise objects with zero direct references first, discard those, and continue finalising the new set of objects with zero direct references. That is, finalise in topological order. This has two problems, one in theory, one in practice. In theory, of course, *a cycle in the graph of objects* to be finalised will prevent a topological sort from succeeding. In practice, the "right" thing to do appears to be to signal an error (at least when debugging) and let the programmer clean this up. People with experience on large systems report that such cycles are in fact exceedingly rare (note, however, that some languages define "finalisers" for almost every object, and that was not the case for the large systems studied - there, finalisers were not too common).

The practical problem is that *finalisers can "revive" dead objects*. Dead objects can certainly refer to live objects, and it is also entirely possible for the code in a finaliser to store a pointer to a currently-dead object into a live object, thus reviving the "dead" object, perhaps even the object on whose behalf the finaliser was being run. This means either that a write barrier must be enforced so that this can be detected, or that after each GC, only those objects that have zero references can be finalised; the rest (those that ought to have zero references after the first batch is recycled) must wait for a subsequent GC. Write barriers are not always an option, and deferring finalisation more or less guarantees that more memory will be consumed and that resources will be slowly reclaimed.

The other approach is to declare that finalisers can be run in any order whatsoever over unreachable storages. This has the unfortunate side-effect of making it difficult to write finalisers, because the other objects to which an object ~Obj~ refers (and upon which its state may depend) may have already been finalised by the time ~Obj~'s finaliser is run. This is especially difficult when the compiler and collector are not cooperating, because what looks like separate memory objects to the collector may in fact be part of what is logically a single object at the source language level (and hence bugs may appear that the programmer has no way of preventing).

Yet another approach is to declare that finalisers shall not revive objects. With a stop-and-copy collector, this is not too hard to detect for debugging purposes; garbage is collected, finalisers are run, and the live objects are scanned for any references to just-finalised objects. Those found can be reported to the programmer. This can fail in a conservative collector, if finalisers write pointer-like bit patterns into non-pointer data.

In the case of Java, the approach taken was /to declare that finalisers are never run more than once per object/; if an object is revived in finalisation, that is fine, but its finaliser will not run a second time. It isn't clear if this is a matter of design, or merely an accident of the first implementation of the language, but it is in the specification now. Obviously, this encourages careful use of finalisation, in much the same way that driving without seat belts encourages careful driving.

One partial solution to this problem is to encourage people to use "the right tools for the job." Languages with GC often include control constructs for running finalisers at certain points in a program's execution. These can be used where timely, certain, finalisation is required. Finalisation associated with garbage collection can be used for those resources that are either abundant-but-not-infinite (like memory) or as a statistical backstop to reduce the loss of resources that are managed by hand (similar to the way in which garbage collection itself can be used as a backstop for manual deallocation).

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
 - [GC FAG -- draft](https://iecc.com/gclist/GC-faq.html)
 - [MemFix: Static Analysis-Based Repair of Memory Deallocation Errors for C](https://prl.korea.ac.kr/papers/fse18.pdf)

---
