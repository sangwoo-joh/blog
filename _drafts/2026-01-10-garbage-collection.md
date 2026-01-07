---
layout: post
published: true
tag: [cs, essay]
title: 가비지 컬렉션 이야기
---

## 목차
{:.no_toc}

* Table of contents
{:toc}

모든 프로그램은 메모리가 필요하다.

자동으로 관리되는 스택은 크기가 제한적이다. 보통 윈도우는 1MB이고 리눅스는 8MB다. 튜닝으로 이 값을 조절할 순 있겠지만 그래도 한계가 있다. 더 큰 크기의 계산을 하려면 스택을 벗어나 힙 메모리가 필요하다. 프로그램은 커널에게 부탁해서 힙 메모리를 얻을 수 있다. 힙 메모리를 가지고 필요한 계산을 끝내고 나면 다 쓴 메모리는 다시 커널에게 돌려줘야 한다. 가상 메모리도 물리 메모리도 모두 유한한 자원이기 때문이다. 제때 안돌려주고 계속 메모리를 얻기만 하면 계속된 페이징, 스와핑, 페이지 폴트, 쓰레싱(Thrashing) 등의 이유로 성능이 계속 곤두박질치다가 결국 커널은 패닉에 빠질 것이다.

보통은 프로그래머가 직접 메모리를 관리하는 코드를 작성한다. 필요한 만큼 커널에게 할당받아서 쓰고 (memory allocation, 메모리 할당), 다 쓰고 나면 다시 커널에게 돌려준다 (free, 메모리 해제). 이 짝을 맞추는 게 기본이다. 그러나 프로젝트의 요구사항이 복잡해지고 프로그래밍 언어의 고급 기능이 많아질수록 (예: 예외 처리, 코루틴), 이 짝을 맞추는 일이 어려워진다. 무엇보다 사람은 실수를 저지른다. 이미 돌려준 메모리를 안 돌려준 줄 알고 사용해버리거나 (Use After Free), 까먹고 돌려주지 않은 채로 계속 있거나 (Memory Leak), 같은 메모리를 여러 번 돌려주는 (Double Free) 등의 실수는 너무도 흔해서 각각에 이름이 붙을 정도다. 그리고 이런 오류는 적어도 프로그램의 성능을 깎아먹거나, 치명적인 보안 취약점을 노출시키거나, 프로그램을 죽여버린다.

그래서 자동으로 메모리를 관리하는 방법이 연구되기 시작한다. 최초의 자동 메모리 관리 방법은 1959년에 LISP 프로그래밍 언어에 도입되었다. LISP의 창시자이자 인공지능 연구자 존 매카시 님의 [관련 논문](https://www-formal.stanford.edu/jmc/recursive.pdf)의 27페이지에는 트레이싱 컬렉션(Tracing Collection)에 대한 기초적인 아이디어, 즉 *프로그램의 어떤 부분에서도 찾을 수 없는(닿을 수 없는) 데이터는 버려진 것으로 간주하고 나중에 재활용하는 방법*을 설명하고 있다.

> ... Such a register may be considered abandoned by the program because its contents can no longer be found by any possible program; hence its contents are no longer of interest, and so we would like to have it back on the free-storage list. ...

뱀발로 7번 각주가 꽤 재밌는데:

> We already called this process "garbage collection", but I guess I chickened out of using it in the paper - or else the Research Laboratory of Electronics grammar ladies wouldn't let me.

논문에서는 이렇게 각주에 딱 한번만 등장한 "가비지 컬렉션"이라는 이름이 지금은 표준적인 이름으로 널리 쓰이고 있다는 사실이 아이러니하다.

# 왜 필요할까?
"애초에 가비지 컬렉션이 왜 필요함? 처음부터 메모리 이슈 없게 잘 짜면 되는 거 아님?" 이라고 생각할 수 있다. 과거의 나도 그랬다. 하지만, 비단 가비지 컬렉션이 아니더라도, 메모리 관리를 위한 다양한 방법론이 여전히 연구 되고 있는 데에는 다 이유가 있다.

## 과거와 지금

먼저 역사적인 배경을 한번 살펴보자. 최초의 가비지 컬렉션이 LISP 언어에 도입된 이유 중 하나는, 당시 메이저 언어 였던 ALGOL 언어에서 댕글링 포인터 문제, 그러니까 쓰던 메모리를 이미 해제했는데 그걸 모른채로 프로그램의 다른 부분에서 해제된 메모리 주소를 계속 갖고 있다가 사용해버리는 심각한 버그가 큰 이슈였다 (Use After Free). 그 당시 프로그래머라면 정말 똑똑한 소수의 선택된 사람들일텐데, 그런 친구들에게도 수동으로 메모리를 관리하는 일은 쉽지 않았던 것이다.

**근데 이 문제는 지금도 해결되지 않았다.** 오히려 인터넷이 발전하면서 더 심각해졌다. Use After Free 버그는 이제 단순히 프로그램을 죽이는 데서 그치지 않고 프로그램의 보안 취약점이 되어 더 큰 문제를 만든다. 인터넷이 발전하면서 많은 것들이 가능해졌지만, 그로 인해 프로그램의 보안 취약점은 더이상 단순한 버그가 실제적인 위협이다. [마이크로소프트의 한 조사](https://www.microsoft.com/en-us/msrc/blog/2019/07/we-need-a-safer-systems-programming-language)에 따르면 매년 CVE (공개적으로 알려진 보안 취약점에 아이디를 붙이는 시스템) 의 약 70%가 메모리 안전정 문제라고 한다. [구글에서도 비슷한 결과](https://www.zdnet.com/article/chrome-70-of-all-security-bugs-are-memory-safety-issues/)를 발표한 적이 있는데, 크롬의 심각한 보안 관련 버그 중 70%가 메모리 관련 오류, 그 중 절반이 Use After Free였다고 한다.

1960년대에 발견된 문제가 2020년대에도 여전히 보안 취약점의 대다수를 차지한다는 사실은 수동으로 메모리를 관리하는 것이 얼마나 어려운지를 보여준다.

## 문제의 난이도

"메모리 이슈 없게 잘 짜면 되는 거 아님?"이 얼마나 어려운지를 보여주는 또 다른 명확한 근거는 바로 이 문제 자체의 본질적인 고난도이다. 메모리 오류의 대부분은 결국 커널로부터 힙 메모리를 할당 받아서 (`malloc`) 쓴 다음에 이걸 적절한 타이밍에 돌려줘야 (`free`) 하는 이 *타이밍*이 어긋나서 발생하는 것이다. 그런데 이렇게 메모리를 할당하고 돌려주는 작업이 필요한 시점을 정확하게 예측하는 것은 **이론적으로 불가능하다**. 다시 말해, "여기서 할당되어서 사용되던 메모리가 코드의 여기에서 딱 사용이 끝날테니 여기다가 `free`를 넣으면 되겠다" 라는 분석이 원천적으로 불가능하다. 왜냐하면 코드만 가지고는 할당된 메모리의 수명을 알아내는 알고리즘은 만들 수 없기 때문이다 (Undecidable).[^2] 그렇다고 프로그램이 끝나는 시점에 한꺼번에 메모리를 돌려줘버리면 애초에 메모리를 관리하려는 의미가 없지.

[^2]: 컴퓨터 과학의 한계를 증명한 정리 중 하나인 [라이스의 정리](https://en.wikipedia.org/wiki/Rice%27s_theorem)에 따르면, 프로그램의 모든 non-trivial semantic 성질은 결정 불가능하다. 그래서 Rust의 경우 언어의 표현력을 제한해서 이 문제를 결정 가능한 수준으로 축소해서 풀고, 컴파일러가 추론이 불가능하면 프로그래머에게 명시적인 라이프타임 어노테이션을 요구한다.

좀더 쉬운 문제로, "어떤 객체의 메모리는 크기는 이정도이고 수명은 이정도다"라는 정보가 미리 알려져 있을 때 모든 객체들의 할당과 해제 시점을 잘 배치해서 메모리 사용량을 최소화 하도록 하는 *동적 스토리지 할당 (Dynamic Storage Allocation, DSA)* 문제를 한번 생각해보자. 그런데 이 문제는 NP-Complete 임이 증명되어 있다. 즉, 메모리를 잘 배치해서 최소한의 메모리만 사용하도록 계산하는 알고리즘이 있긴 있는데, 언제 끝날지 모른다. 다시 말해 메모리의 생명주기(Lifetime)가 "이미 알려져 있는" 경우에도 최적의 배치를 찾는 것이 무척 어렵다는 말이다.

정리하면, 메모리를 할당하고 해제하는 작업을 정확하게 계산하는 것은 이론적으로 불가능하고, 그것보다 더 쉬운 문제의 경우에도 무척 어렵다.

## 인지적 부하

내가 중요하게 생각하는 점 중 하나는 바로 인지적인 부하이다 (Cognitive Load). 현대의 대규모 소프트웨어를 개발하는 일은 어렵다. 설령 작은 규모를 혼자서 만들더라도 현재의 나와 미래의 나는 다른 사람이다. **코드는 쓰이는 것보다 훨씬 더 많이 읽힌다**. 관련해서 많은 격언들이 있다. 엉클 밥의 "읽기와 쓰이게 소요되는 시간의 비율은 10:1을 훨씬 상회한다" 라던지, 귀도 반 로썸의 "코드는 쓰이는 것보다 더 자주 읽힌다" 라던지. 아무튼, 어떤 코드 베이스를 이해하는 작업은 어렵다. 예를 들어, 어떤 프로젝트의 코드 한 줄을 이해하고 싶다고 하자. 만약 이 코드가 속한 함수나 파일을 넘어서, 코드 베이스 전체, 심지어는 프로젝트가 의존하고 있는 패키지를 다 따라가서 모든 것들을 고려해야 한다면, 이는 결코 쉬운 작업이 아니다 (Global Reasoning). 반면에, 그 코드의 근처의 로직만 살펴봐도 충분하다면, 이 작업은 한결 수월해질 것이다 (Local Reasoning).

이렇게 근처 코드만 봐도 로직을 이해할 수 있는, 진정한 의미의 "모듈화된 프로그래밍 (Modular Programming)"을 위해서는 가비지 컬렉션이 필요하다. 모듈 사이에 의존성이 생기는 것을 막을 수는 없다. 하지만 모듈이 계산을 위해 메모리 할당을 필요로 할 때 이 메모리의 소유권에 대한 분쟁이 발생한다 (Ownership). 특히 모듈 객체의 생명주기는 **전역적인 속성**이다. 예를 들어, 모듈 A가 할당하는 어떤 객체를 모듈 B와 C가 공유할 때, 이 객체가 언제 해제되어야 하는지를 알기 위해서는 이 세 모듈을 **모두** 추적해야만 한다. 그런데 이렇게 모듈의 핵심 로직만이 아니라 모듈이 사용하는 메모리도 고려해야 한다면, 이해의 난이도가 급격하게 상승한다. 그 외에도 모듈 객체의 메모리를 안전하고 정확하게 해제하기 위한 다양한 추가 구현이 런타임에 상당한 비용을 초래할 수도 있다. 멀티 쓰레드 어플리케이션이면 동기화도 고려해야 한다. 아무튼 간에 복잡해진다.

결국 언어 설계는 안전성, 표현력, 성능, 사용성 사이의 트레이드오프를 고려해야 한다. 가비지 컬렉션은 약간의 성능을 희생하면서 안전성, 표현력, 사용성을 모두 챙겨갈 수 있는 좋은 선택지이다.

# 추상화
그럼 이제 본격적으로 가비지 컬렉션에 대해서 얘기해보자.

먼저 존 매커시 님의 가비지 컬렉션에 대한 아이디어를 다시 가져와 보자. "프로그램의 어디에서도 닿지 않는 메모리는 더 이상 쓰이지 않는 것으로 간주하고, 이것들을 따로 모아뒀다가 나중에 재활용한다." 즉, 가비지 컬렉션을 두 단계로 나눌 수 있다.
 1. **가비지 찾기 (Garbage Detection)**: 살아있는 객체(Live Object, Reachable Object)와 가비지 객체(Dead Object, Unreachable Object, Garbage)를 구분한다.
 2. **가비지 수집 (Garbage Collection)**: 가비지 객체의 메모리를 수집한다. 곧바로 해제할 수도 있고, 아니면 따로 모아놨다가 재활용할 수도 있다.

실제로 이 두 단계는 완전히 구분되지 않은 채로 얽혀 있을 수 있고, 특히 수집 방법은 찾는 방법에 크게 의존하는 경우가 많다.

가비지 컬렉션 알고리즘에 대해서 이야기 하기 전에, 공통적으로 나오는 몇 가지 기본적인 개념들을 알아둘 필요가 있다.

## 루트 집합
실행 중인 프로그램이 즉시 사용할 수 있는 객체를 **루트 집합(Root Set)**이라고 한다. "즉시 사용할 수 있다"는 뜻은 어떤 포인터를 따라가지 않고도 곧바로 접근 가능하다는 뜻이다. 예를 들면, 지금 실행 중인 함수의 스택에 올라가 있는 변수, 글로벌 변수, 정적 모듈, 등이 있다.

이걸 바탕으로 앞의 두 단계 추상화를 다시 생각해보자. 그러면 "가비지 찾기" 단계는 곧 "루트 집합에서부터 시작해서 닿을 수 있는 모든 객체"를 찾는 문제가 된다[^4].

[^4]: 정확히는, 이렇게 찾은 객체들을 전체 메모리에서 빼고 남은 메모리를 가비지로 간주할 수 있다.

## 컬렉터와 뮤테이터
보통 가비지 컬렉션은 프로그래밍 언어에 기본적으로 장착되어 있거나 어떤 라이브러리에 핵심 컴포넌트로 구현되어 있다. 이때 가비지 컬렉션을 담당하는 에이전트를 가비지 컬렉터, 혹은 그냥 컬렉터(Collector)라고 부른다. 근데 흥미롭게도 가비지 컬렉션 연구자들은 사용자 프로그램을 "뮤테이터(Mutator)"라고 부르는데, 왜냐하면 사용자 프로그램이 컬렉터가 관리해야 하는 객체들의 메모리 상태를 계속해서 바꾸기 (mutate) 때문이다. 철저하게 가비지 컬렉션 입장에서 이름 지은 거라서 웃겼다.

## 박싱 (Boxing)
가비지 찾기 단계가 완료되고 나면 가비지 수집 단계에서 컬렉터가 각각의 객체에 대해서 "얘는 가비지임" 혹은 "얘는 가비지 아님"을 알 수 있어야 한다. 이게 가능하려면 해시 테이블에 객체마다 메타데이터를 기록하던지, 아니면 객체마다 추가로 메타데이터를 덧씌워서 기록하던지, 둘 중 하나밖에 없다. 해시 테이블은 생각보다 비용이 크고 캐시 친화적이지 못하기 때문에 대부분의 가비지 컬렉션은 후자의 방법, 즉 객체마다 메타데이터를 덧씌우는 방식을 택하는데 이를 **박싱**이라고 한다.

박싱은 그 이름처럼 객체를 어떤 상자(Box)에다 넣고 상자 겉면에 객체와 관련된 메타데이터를 기록하는 방법으로 이해할 수 있다. 기록할 메타데이터로는 객체가 살아있는지 죽었는지, 객체가 얼마나 사용되고 있는지, 얼마나 큰 객체인지, 어떤 타입의 객체를 담았는지 등이 있겠다. 당연하지만 이로 인해 발생하는 오버헤드는 피할 수 없다. 어쩔 수 없는 트레이드 오프이다.

---

가비지 컬렉션 알고리즘은 크게 두 갈래로 나뉜다.

각 객체의 참조 횟수를 추적해서 0이 되면 즉시 수집하는 **레퍼런스 카운팅(Reference Counting)**과, 주기적으로 지금 쓰고 있는 객체와 안쓰는 가비지를 추적해서 가비지만을 수집하는 **트레이싱 컬렉션(Tracing Collection)**이 있다.

# 레퍼런스 카운팅
레퍼런스 카운팅은 두 단계 추상화를 다음과 같이 구현한다.
 1. 가비지 찾기: 모든 객체를 박싱해서 각 객체마다 지금 사용되고 있는 횟수, 즉 참조 횟수를 기록한다. 프로그램이 실행되는 동안 누가 객체를 참조하면 횟수를 증가시키고 객체 사용이 끝나면 횟수를 감소시킨다. 그러다가 참조 횟수가 0이되는 즉시 가비지로 판단한다.
 2. 가비지 수집: 참조 횟수가 0인 객체의 모든 메모리를 해제한다.

이 방식의 특징은 위의 1, 2가 동시에 일어난다는 점이다.

레퍼런스 카운팅은 여러가지 장점이 있다. 일단 아이디어가 간단해서 이해하기 쉽다. 그래서 메모리 관리 뿐 아니라 리소스 관리에도 종종 쓰인다. 그리고 객체를 다 쓴 *즉시* 수집하기 때문에 객체의 수명이 명확해서 메모리를 필요한 만큼만 사용하는 편이다. 이 덕분에 객체에 대한 종료 처리도 예측한 대로 동작하는 편이다 (Finalisation). 또, 통상적으로 응답성이 좋은 편이라 주로 실시간 시스템에서 채택되었다. 끝으로 아이디어가 간단한 만큼 구현도 간단하다고 하는데... CPython 구현 코드에서 레퍼런스 카운터를 [늘리거나](https://github.com/search?q=repo%3Apython%2Fcpython%20py_incref&type=code) [줄이는](https://github.com/search?q=repo%3Apython%2Fcpython+py_decref&type=code) 코드를 검색하면 엄청 많은 곳에서 발견되어서, 개인적으로 그렇게 쉬울 거라는 생각은 들지 않는다.

그런데 주변을 둘러보면, 레퍼런스 카운팅**만**을 가비지 컬렉션으로 채택한 언어나 프로그램은 거의 없다. 그 이유는 다음과 같은 몇 가지 근본적인 한계 때문이다.

## 정확성의 한계

가장 큰 한계는 바로 그 유명한 순환 참조 문제다 (Circular Reference). 어떤 두 객체가 서로를 참조해버리면 다른 모든 곳에서 이 객체에 대한 작업을 끝내더라도 이들의 참조 횟수는 항상 1(이상)이기 때문에 절대로 수집되지 않는다 (Memory Leak). 이런 경우가 얼마나 많겠냐 싶은데, 실제로 꽤 많다. 예를 들면 LRU 캐시 등의 구현에 사용되는 더블 링크드 리스트나, 계산 편의를 위해 부모 노드로 가는 포인터를 추가한 트리의 노드 등이 있다.

즉, 레퍼런스 카운팅은 항상 **가비지의 보수적인 근사값(Conservative Approximation)**만을 판단한다는 한계가 있다. 어떤 객체의 참조 횟수가 0이면 항상 가비지이지만, 그 역은 참이 아닐 수도 있다. 이로 인해 모든 가비지를 수집할 수 없게 되고 프로그램은 메모리를 누수한다.

## 성능 오버헤드

생각보다 오버헤드가 크다는 단점도 있다.

먼저 박싱을 통해 모든 객체에 "레퍼런스"라는 걸 도입해야 하는데, 말 그대로 **모든** 객체, 즉 언어가 제공하는 원시 데이터 타입과 사용자가 정의하는 타입까지 전부 다 박싱해야 한다. 이로 인해서 객체의 메모리를 미세하게 표현하고 조절하는데 제약이 생긴다. 예를 들어, 항상 메모리에 상주하는 정적 객체를 사용하고 싶은 경우에도 이 객체는 레퍼런스 카운팅 방식으로 박싱 되어 사용될 때마다 레퍼런스를 늘리거나 줄여야 한다. 또는, 금방 사용되고 버려질 것이라는 생명주기를 정확하게 알고 있는 객체의 경우에도 박싱을 하고 사용할 때마다 참조 횟수를 업데이트 해야 한다. 그래서 많은 가비지 컬렉션에서는 이러한 [미세 조정을 할 수 있는 도구](#약한-포인터-weak-pointer)를 제공하기도 한다.

게다가, 참조 "횟수"를 세기 위해서는 헤더에 어떤한 정수 값을 담아야 한다. 그런데 프로그램이 실행되면서 최대 몇 번의 참조가 이뤄질지를 미리 아는 것은 불가능하기 때문에, 적당한 크기의 정수를 선택하는 것도 어려운 문제다. 너무 큰 정수를 선택하면 계산 오버헤드가 있고, 그렇다고 너무 작은 정수를 선택하면 정확한 참조 횟수를 담지 못할 수 있다. 그래서 적은 수의 비트만을 사용해 참조 횟수에 대한 정확도를 희생해서 더 보수적인 근사치를 계산하는 최적화 방법이 연구되기도 했다.

레퍼런스 카운팅 컬렉터가 관리할 객체는 모두 정해진 통일된 형식을 따라 박싱되는데, 보통 참조 횟수나 실제 데이터 크기 등을 메타데이터를 담은 *헤더*와 실제 데이터를 담고 있는 *포인터*로 구성된다. 즉, 모든 데이터는 단순히 접근할 수 있는 값이 아니라 포인터를 따라가야만 알 수 있는 값이 되는데, 이로 인해 [간접적인 메모리 오버헤드](../virtual-memory)가 발생한다. 캐시 미스가 자주 발생할 수 밖에 없다.

결정적으로, 프로그램의 작업량에 비례해서 메모리 관리 오버헤드가 늘어난다. 예를 들어 `a = b + 1` 이라는 코드를 실행한다고 하자. 그러면 `a`는 값이 쓰여지기 때문에 참조 횟수를 증가시키고, `b`는 값을 읽기 때문에 참조 횟수를 줄인다. 참조 횟수가 줄어드는 경우에는 이 값이 0이 되는지도 확인해야 한다. 두 변수를 쓰는 단순한 한 줄의 코드를 실행하는데 두 객체를 모두 업데이트 해야 한다. 그래서 프로그램의 작업량 자체가 많으면 오버헤드도 같이 증가할 수 밖에 없다. 게다가 어떤 커다란 객체의 카운트가 0이 되어서 그 객체를 따라 연결된 수많은 객체들이 모두 다 해제되어야 하는 상황이 오게 되면, 일관되고 예측 가능한 성능이 깨진다는 점도 무시할 수 없다. 이를 피하기 위해서 레퍼런스 카운팅의 최적화 연구에서는 컬렉션과 관련된 연산을 미루는 것들이 많다 (Deferred Reference Counting).

## 메모리 재사용의 어려움

의외로 메모리 재사용이 어렵다는 점도 꼽을 수 있다. 가비지 객체의 메모리를 곧바로 해제하지 않고 임시 저장소에다 잠깐 놔뒀다가 나중에 메모리 할당 요청에 재사용하려고 하자. 만약 이 가비지가 단순한 객체가 아니라 링크드 리스트나 트리같은 복잡한 객체였다면, 가비지와 연결된 모든 객체들을 따라가서 일일이 크기 별로 임시 저장소에 넣어야 하는 오버헤드가 즉시 발생한다. 그래서 장점이었던 좋은 응답성을 잃을 수 있다.

## 모든 작업이 암묵적인 쓰기 연산

개인적으로 겪었던 단점 중 하나는 바로 **객체를 읽는 모든 연산이 암묵적으로 쓰기 연산이 되어버린다**는 것이었다. 이로 인해서 데이터를 단순히 읽기만 하는 것이 원천적으로 불가능하다. 예를 들어 커다란 데이터 덩어리를 여러 프로세스 사이에 읽기만 하는 목적으로 공유하는 경우, 커널이 제공하는 최적화 중 하나인 [쓰기 시 복사(Copy-on-Write)](../virtual-memory#cow-copy-on-write)를 적용하는 것이 불가능해져서 예상했던 것보다 엄청나게 많은 메모리를 잡아먹게 된다. 그래서 병렬 처리에 애를 먹었던 적이 있다. 이럴 때는 다른 라이브러리를 이용해서 읽기만 할 데이터를 공유 메모리에 올리거나 하는 방식으로 우회해야 한다.

모든 연산이 참조 횟수에 쓰기 작업을 해야 하기 때문에, 멀티 쓰레드 환경에서는 필연적으로 경쟁 상태가 발생한다 (Race Condition). 그래서 공유 메모리 병렬 처리 (Shared Memory Parallelism), 다시 말해 멀티 쓰레드 환경에서의 런타임 구현을 더 복잡하게 만든다. 파이썬에서는 구현을 간단하게 하기 위해서 GIL(Global Interpreter Lock)을 도입하기도 했다.

## 레퍼런스 카운팅의 현재

이러한 한계들로 인해서 현대에는 레퍼런스 카운팅만을 도입한 언어는 잘 없다. 보통은 다음 둘 중 하나를 택한다.[^3]
 * 하이브리드 접근: 레퍼런스 카운팅을 기본으로 하되, 순환 참조를 피하기 위해서 보조로 트레이싱 컬렉션을 같이 장착한다. 예를 들면 파이썬과 스위프트가 그렇다.
 * 제약된 레퍼런스 카운팅: 순환 참조를 방지하도록 소유권 규칙을 강제한다. Rust의 `Rc<T>`가 있다.

[^3]: 하지만 레퍼런스 카운팅 "알고리즘" 자체는 유용하게 널리 쓰이는 편이다. 예를 들면, C++의 스마트 포인터나 유니크 포인터가 그러하고, 혹은 정말로 이런 식으로 밖에 관리할 수 없는 외부 리소스들, 예를 들어 파일 식별자에 대해서 자동으로 `open`/`close` 쌍을 호출할 때 쓰이기도 한다.

그리고 레퍼런스 카운팅은 생각보다 최적화할 여지가 많지 않은 것 같다. 왜냐하면 가비지 컬렉션과 관련된 연구는 주로 아래에 설명할 트레이싱 컬렉션을 기반으로 하는 것이 많기 때문이다.

# 트레이싱 컬렉션
트레이싱 컬렉션은 이름 그대로 가비지를 "추적해서" 수집한다. 구체적으로는 가비지 컬렉션 추상화의 두 단계, 가비지를 찾는 단계와 가비지를 수집하는 단계를 정직하게 구현한다. 그래서 가비지 찾기와 수집이 각 객체에 대해서 한꺼번에 일어나는 레퍼런스 카운팅과는 다르게, 트레이싱 컬렉션은 전체 객체에 대해서 두 단계가 순차적으로 수행된다.

트레이싱 컬렉션에는 다양한 알고리즘들이 연구되어 왔다. 이들의 공통된 특징 중 하나는 가비지를 찾고 수집하는 방식 뿐만 아니라, 수집한 가비지 메모리를 곧바로 해제하지 않고 이후의 할당에 재활용하는데에도 초점이 맞춰져 있다는 것이다. 메모리 할당과 수집한 메모리를 재사용하는 것은 동전의 양면과도 같아서, 트레이싱 컬렉터는 "가비지 메모리를 관리하기 위한 시스템"이라고 생각할 수도 있다.

## Mark-Sweep Collection
마크 스윕 컬렉션은 이름 그대로 마킹 페이즈와 스위핑 페이즈를 구현한 알고리즘이다.
 * 가비지 찾기: 마킹 페이즈. 루트 집합으로부터 시작해서 닿을 수 있는 모든 객체를 추적해서 "살아있는 객체"로 구분한다.
 * 가비지 수집: 스위핑 페이즈. "살아있는 객체"가 아닌 모든 객체들은 죽은 객체, 즉 가비지로 판단할 수 있다. 가비지 객체들은 곧바로 해제하지 않고 수집해서 이후 할당에 재활용한다.

이건 어디까지나 마크 스윕 컬렉션에 대해서 추상적으로 설명한 것이다. 구체적으로 파고 들면 다음과 같은 것들을 고려해야 한다.

### Free List
가비지 메모리를 따로 수집해서 관리하다가 이후 할당에 다시 사용하는 것은 매우 적절해보인다. 그런데, 이걸 어떻게 구현할까?

오래된 LISP에서 도입된 방법은 바로 프리 리스트이다 (Free List).

### 세 가지 색깔 (Tri-Colour Scheme)
마크-스윕 컬렉션(과 그 변형)은 저마다의 방식으로 객체의 상태를 구분하는데, 가장 널리 쓰이는 방법 중 하나는 아래의 세 가지 색깔을 이용하는 방식이다.

 * 흰색(Unmarked): 컬렉터가 관심있는 대상이다.
   * 마킹 페이즈 시작 전: 모든 오브젝트의 초기 상태를 나타낸다. 컬렉터는 루트 집합으로부터 닿을 수 있는 흰색 객체들을 하나씩 보면서 색깔을 칠해나간다.
   * 마킹 페이즈 완료 시: 마킹이 끝났는데도 여전히 흰색인 객체들은 루트 집합으로부터 닿을 수 없는 객체들 **(Unreachable Objects)**, 즉 **가비지**를 뜻한다.
   * 스위핑 페이즈에서: **가비지 수집 대상**이다. 흰색 객체의 메모리를 프리 리스트에 모아놨다가 나중에 재사용한다.
 * 회색(In-Marking): 마킹 페이즈에서만 임시로 쓰인다. 어떤 객체가 루트 집합으로부터 닿긴 했는데 아직 그 자식들(포인터를 따라갈 수 있는 객체들)까지는 살펴보지 않은 상태를 뜻한다.
 * 검은색(Marked): 루트 집합으로부터 닿을 수 있는 객체들 (**Reachable Objects**), 즉 "살아있는 객체들 (Live Object)"을 뜻한다. 얘네들은 아직 프로그램이 사용하고 있는 객체일 수 있기 때문에 스위핑 페이즈에서 살려둔다. 스위핑이 끝나고 나면 다시 색깔을 뒤집어서 흰색(초기 상태)으로 돌려둔다.

이걸 바탕으로 트레이싱 컬렉션은 어떤 실행 시점에서 메모리 상의 객체들로 이뤄진 그래프를 탐색하면서 색깔을 칠하는 문제로 생각해볼 수 있다. 이번에는 이해를 돕기 위해서 그림을 한번 그려봤다. 각 그림의 설명은 그림 밑에 적었다.

![초기상태](/assets/img/mark-init.svg)
제일 처음에는 모든 노드(객체)들이 흰색이다. 객체를 따라 다른 객체에 접근할 수 있다면 엣지가 있다 (Reachable).

<br />

![마킹](/assets/img/mark-0.svg)
마킹 페이즈는 루트 집합에서 시작한다. 가장 먼저 노드를 하나씩 방문하면서 회색으로 칠한다.

<br />

![마킹](/assets/img/mark-1.svg)
자식 노드로 넘어갈 때 부모 노드는 검은색으로 칠하고 자식 노드는 회색이 칠한다.

<br />

![마킹](/assets/img/mark-2.svg)
이렇게 흰색 -> 회색 -> 검은색의 물결이 진행되는데, 모든 닿을 수 있는 노드는 회색을 기준으로 한쪽은 흰색 다른 한쪽은 검은색인 모습이 된다.

<br />

![마킹 끝](/assets/img/mark-n.svg)
마킹 페이즈의 모든 탐색이 끝나고 나면 검은색 노드는 살아있는 객체이다. 그리고 흰색 노드들은 안전하게 가비지로 판단할 수 있다.

<br />

![스위핑](/assets/img/sweep.svg)
스위핑 페이즈에서는 컬렉터가 관리 대상 메모리 구역을 전부 훑으면서 흰색 노드를 수집한다. 이 노드들은 나중에 재활용 하기 위해서 프리 리스트에다 추가한다.

<br />

![스위핑 끝](/assets/img/sweep-end.svg)
스위핑 페이즈에서 가비지 노드들을 다 프리 스토리지 리스트에 넣고 나면, 이번 컬렉션을 살아남은 검은 노드들이 다음 컬렉션에서 관리될 수 있도록 다시 흰색으로 칠한다.

실제 구현은 더 디테일한 사항이 많지만, 하이 레벨에서는 이렇게 세 가지 색깔로 마크 스윕 컬렉션을 이해할 수 있다.

### Stop-The-World Coordination
그런데 이렇게 색을 "칠하는" 작업은 노드에다가 색을 표현하는 값을 "쓰는(write)" 작업이다. 게다가 칠해야 할 노드가 한두개가 아니다. 이로 인해 다양한 문제가 생긴다.

일단 이 노드(객체)들은 컬렉터만 건드리는 게 아니다. 뮤테이터(사용자 프로그램)도 건드린다. 그런데 만약에 뮤테이터와 컬렉터가 동시에 이 객체들을 건드리면, 크게 두 가지 문제가 발생한다.

가장 치명적인 이슈는 바로 **Missing Mark**이다. 살아있는 객체가 잘못 수집될 수 있다. 왜냐하면, 마킹 페이즈에서 타이밍 이슈로 인해 실제로 살아있는 객체가 검은색으로 칠해지지 않을 수 있기 때문이다. 이건 그림으로 예를 들면 바로 이해할 수 있다.

먼저 메모리에 A -> B -> C 의 노드가 있고 컬렉터가 A를 검은색으로 칠하고 이제 B를 방문해서 회색으로 칠한 상태라고 하자.

이때 갑자기 뮤테이터가 B -> C의 링크를 끊어버리고 A와 C를 연걸해서, A -> C 로 수정해버리면 어떻게 될까?

컬렉터는 B에 매달린 자식 노드가 없기 때문에 B를 검은색으로 칠하고 다음 노드를 찾아 떠나가버린다. 그런데 A -> C의 새로운 링크가 있음에도 불구하고, A를 이미 검은색으로 칠했기 때문에 C는 절대로 칠해지지 않는다. 그래서 C는 닿을 수 있는 살아있는 객체인데도 불구하고 흰색으로 남겨져 있다가, 곧이은 스위핑 페이즈에서 수집되어 버린다.

즉, 뮤테이터와 컬렉터가 동시에 동작하는 경우에는 마킹 페이즈의 정확성이 깨져버린다. 그래서 이를 막기 위해서 마크 스윕 컬렉션은 그 악명 높은 STW(Stop-The-World) 조정을 도입한다. 프로그램을 일시정지 하는 것이다. 좀더 정확하게는, 컬렉터가 마킹 페이즈에 들어가서 노드를 색칠할 때에는 뮤테이터를 멈춘다. 스위핑 페이즈에서는 이미 마킹 페이즈에서 안전하게 가비지와 살아있는 객체를 구분했기 때문에 멈출 필요는 없다.

### Incremental Collection
무작정 STW를 해버리면 마킹 페이즈에서 프로그램이 멈추게 되고 (Pause Time) 이로 인해 프로그램의 응답성을 예측할 수 없게 된다. 그래서 실시간 환경에 쓸 수 없다.

이걸 해결하기 위해서 도입한 것이 바로 증분 컬렉션(Incremental Collection)이다. 마킹을 전체 다 한꺼번에 하는게 아니라, 마킹이랑 스위핑 페이즈를 일단 나누고, 각 단계를 잘라서 (Slicing) 조금 씩 진행해서 (Incremental) 사용자 프로그램이 너무 긴 정지 시간 (Pause Time)을 겪지 않고 반응성이 좋도록 한다.

#### Write (Read) Barrier
Incremental을 도입하면 발생하는 문제를 해결하기 위해서 포인터 쓰기 연산에 도입되는 condition check. 컴파일러가 도와줘야 함. Barrier 라는 이름이 붙은 컬렉션은 incremental이 원조임.

앞의 세 가지 색깔 스킴을 다시 떠올려보자. 그러면 당연히 검은색에서 흰색으로 가는 포인터가 없어야 한다. 근데 incremental하게 하면, 컬렉터가 동작하다가 잠깐 멈추고 뮤테이터가 객체 상태를 변경할 때 이 불변식을 지켜야한다. 예를 들어 컬렉션 도중 A 가 검은색으로 칠해졌고 그 자식들이 회색으로 칠해졌다고 하자. 뮤테이터가 A -> C(검은색 -> 회색)로 포인터가 있던 걸 B -> D (둘 다 흰색)랑 교환한다고 하자. 이러면 A(검은색)은 D(흰색)를 가리키게 되고, B(흰색)은 C(회색)를 가리키게 된다. 그리고 D를 가리키는 유일한 포인터는 A가 된다. C는 B(흰색)에 의해 다시 Reachable 하게 되고, D는 A 외에는 포인터가 없는데 A가 이미 검은색(GC Reachability Traversal이 끝났음)이라서 절대 Reachable하지 않게 된다. 이러고 GC Marking이 끝나면 Sweeping 때 D는 흰색이라서 가비지로 간주되어 회수되는데 원래는 회수되면 안되는 애다. 그래서 이 invariant가 필요하다. 그래서 이걸 지키기 위해서 모든 포인터 쓰기 연산에 배리어를 도입한 것임.

A write barrier is a mechanism for *executing some memory management code* when a write to some object takes place (that object is then "behind the write barrier," or, informally, "write barrier-ed", or, sloppily, "write-protected"). It can take the form of in-lined code (if memory management is integral to the compiler), or a memory-protection fault which is handled by the memory management code. There are also "read barriers," the nature of which is obvious.

The roles a write barrier can play in GC are a little trickier to explain to a novice, but I'll give it a stab.

1. Consider a simple generational stop-and-collect collector. "Generational" means that data is partitioned into /old/ and /new/. This partition is useful to the GC for two reasons: (a) because data tends to die young, collecting just new data will probably free a lot of space, and (b) because pointers tend to point from new objects to old objects, and not vice versa, it is cheap to find all the pointers to new objects.
   *Property (b) is only true if you can tell when a pointer to a new object has been written into an old object*. Otherwise you have to scan all the old objects to find pointers to new objects, which loses one of the main advantages of generational GC. So you put the old data behind a write barrier, and record those writes. When you come to GC the new data, you know the /only pointers from old to new are those which you have recorded/.
2. Consider a tracing GC which is incremental or concurrent, i.e., the user's program or the 'mutator' can run before the GC is complete. Now there is an invariant: *black objects do not point to white objects*. If the mutator writes a white pointer into a black object, this invariant is broken and the GC can fail. There are two basic solutions: prevent the mutator from seeing white objects ("read barriers"), or prevent the mutator from writing white pointers into black objects ("write barriers"). *The write barrier solution puts the black objects behind a write barrier*. When a white-on-black write takes place, there are various fixes: incrementally grey the white object, re-grey the black object, etc.
   (Note) For a tracing collector, marking or copying, one conceptually colours the data white (not yet seen by the collector), black (alive and scanned by the collector), and grey (alive but not yet scanned by the collector). The collector proceeds by scanning grey objects for pointers to white pointers. The white objects found are turned grey, and the grey objects scanned are turned black. When there are no more grey objects, the collection is complete, and *all the white objects can be recycled*.

#### Snapshot-At-The-Beginning Invariant
Incremental Collection의 또 다른 문제점은 컬렉터가 멈춰있는 동안 뮤테이터가 수많은 살아있는 객체를 추가할 수 있다는 점이다. 그래서 이론적으로는 마킹 페이즈가 끝나지 않을 수 있다. 즉, 컬렉터가 열심히 그래프를 색칠해 나가다가 잠깐 멈추고 뮤테이터한테 턴을 넘겨줬을 때 뮤테이터가 그래프에 새로운 닿을 수 있는 살아있는 객체들을 잔뜩 추가해버린 다음 다시 턴을 컬렉터에게 넘겨주고를 끊임없이 진행한다면 충분히 가능하다.

그래서 이 문제를 해결하기 위해서 도입한 불변식이 바로 Snapshot-At-The-Beginning (SATB) Invariant, 우리 말로 하면 "(마킹) 시작할 때의 상태를 스냅샷으로 찍고 이거만 본다"는 것이다. 마킹 페이즈를 시작하는 순간 전체 그래프의 스냅샷을 찍어서 여기에 찍힌 노드들만 추적해서 마킹을 하는 방법이다. 이렇게 하면 **반드시 마킹 작업이 끝난다**는 것이 보장되어서 효율적인 컬렉션이 가능하다.

---

하지만 이 외에도 전통적인 마크 스윕 컬렉션에는 주요한 몇 가지 문제가 있다.

가장 먼저 메모리 단편화[^5]. 위의 그림에서는 그냥 그래프의 노드로 표현했지만 실제로는 힙의 어떤 연속된 구간에 할당되는 메모리들이고, 컬렉터는 관리할 메모리 영역의 시작과 끝을 알아야 한다. 그래서 살아있는 객체와 (수집되는) 가비지 객체가 뒤섞여 있어서 나중에는 큰 크기의 메모리를 할당하기 어려워질 수 있다. 프리 리스트를 여러 크기 별로 만들고 비슷한 크기끼리 수집하는 일종의 크기 별 메모리 풀을 이용해서 이걸 완화할 순 있지만 그래도 어렵다. 그래서 필요에 따라 더 많은 객체를 할당하고 나중에 컬렉터가 일을 더 많이해서 메모리를 필요한 만큼 타이트하게 관리할지, 아니면 아예 처음부터 커다란 메모리 덩어리를 할당한 다음 이걸 쪼개어 관리하면서 단편화 위험을 줄이되 메모리를 조금 낭비할지, 이 트레이드 오프 사이에서 어떤 시스템이 될지를 선택해야 한다.

또 다른 문제는 컬렉터가 가비지를 수집하는 스위핑 페이지에서 **관리하는 메모리 구역 전체**를 살펴봐야 한다는 것이다. 이건 근본적으로 "마킹"이 "살아있는 객체"를 구분하는 것인 반면 "스위핑"이 관심있는 대상은 그 반대인 "죽은 객체"라서, 어쩔 수 없는 한계다.

마지막으로 전반적으로 관리되는 메모리가 캐시 친화적이지 않다는 문제점이 있다. 객체들은 한번 할당되고 나면 거기 계속 남아있고, 이것들 사이에 있던 가비지가 수집되어 이후 할당에 쓰이게 되면, 서로 용도와 수명주기가 다른 객체들이 섞이게 된다. 그래서 계산을 위해 이들 객체에 접근하는 작업의 지역성이 나빠서 캐시 친화적이지 못해 성능의 손해를 본다. 게다가 컬렉션이 진행될수록 살아있는 객체들의 메모리 분포가 나빠질 수 있는데, 많은 객체를 필요로 하는 프로그램의 경우 마킹 페이즈에서 살펴봐야 하는 노드(객체)들이 서로 너무 먼 곳에 떨어져 있게 되면 닿을 수 있는 객체를 살펴보기 위한 그래프 탐색 역시 캐시 친화적이지 않아서 성능에 큰 손해를 보게 된다.

물론 이것들은 다양한 최적화 기법을 통해서 해결하거나 우회할 수 있다.

## Mark-Compact Collection
마크 스윕 컬렉션의 단편화 문제를 해결하기 위해서 압축(Compact) 단계를 도입한 컬렉션 방법이다.

## Copying Collection
메모리를 두 덩어리로 나눈 다음 순차적으로 번갈아가면서 왔다갔다 하는거.

## Generational Collection
1980년대 실시간 어플리케이션 개발에 쓰이던 Smalltalk이라는 언어가 있었는데 얘가 트레이싱 컬렉션을 탑재한 가비지 컬렉션 언어였다. 하지만 여러가지 한계로 인해서 당시 구현된 STW Coordination의 긴 정지 시간으로 인해 "실시간"을 달성하는 게 쉽지 않았다고 한다. 예를 들어, 게임이나 애니메이션을 만드는데 갑자기 GC가 초단위의 시간을 멈춰버리면 사용자들은 화가 날 것이다.

그래서 이 문제를 해결하기 위한 다양한 연구가 이루어졌고, 그 중에서 지금까지도 가비지 컬렉션 뿐만 아니라 수많은 메모리 관리 기법에 커다란 영향을 남긴 것이 바로 David Ungar의 **"세대 가설(Generational Hypothesis)"**이다. "대부분의 객체는 (다 쓰고 나면) 빨리 죽는다 (Most objects are die young)"는 것을 경험적으로 관찰한 것인데, 실제 프로그램의 메모리 사용 패턴을 분석해보니 언어나 프로그램에 상관없이 대부분(80-98%)의 객체는 잠깐만 살아 있다가 사라지고 일부 객체들만이 오래 살아남는다는 놀라운 발견이었다.

세대 가설은 가비지 컬렉션의 패러타임을 완전히 바꿔버렸다. 이후 나온 가비지 컬렉션은 이 가설에 근거해서 아이디어를 체계화해서 컬렉터가 관리하는 힙 메모리를 수명주기를 기준으로 두 개 이상의 세대로 나누고 각각의 세대마다 메모리 관리 알고리즘을 다르게 적용하여 최적의 성능을 내도록 하는 방향으로 진화가 일어난 것이다.

대부분의 GC 언어는 두 개의 세대를 운영한다.
 * 첫 번째 세대: 모든 객체가 처음 할당되는 곳이다. 세대 가설에 따라 여기 할당된 객체들은 대부분 살아남지 못하고 수집될 것이다. 언어마다 명칭이 다른데 마이너 힙, 어린 힙, Generation 0, 에덴 공간 등 다양한 재밌는 이름으로 불린다.
 * 두 번째 세대: 첫 번째 세대를 살아남는 객체들이 옮겨지는 곳이다. 여기까지 온 객체들은 훨씬 더 오래 살아남는 경향이 있다. 그래서 이 세대의 메모리에 가비지 컬렉션이 동작하게 되면 첫 번째 세대보다는 수집되는 비율이 적을 수 있다. 메이저 힙, 성숙한 힙, Generation 1, 생존자 공간 등으로 불린다.

세 개 이상의 세대를 가진 가장 성공적인 언어는 바로 C#(.NET)이다. 닷넷은 총 세 개의 세대와 하나의 별도 힙을 관리하는데,
 * Generation 0: 첫번째 세대.
 * Generation 1: 첫번째 세대를 살아남은 중간 세대. 버퍼 역할을 한다.
 * Generation 2: 마지막 세대. 길게 살아남은 객체들이 여기 있다.
 * LOH(Large Object Heap): 85KB 이상의 큰 객체는 곧바로 여기에 할당되며 별도로 관리한다.

세대 가설에 따르면 세대가 지나갈수록, 즉 Generation 0에서 살아남아 Generation 1, Generation 2로 갈수록 살아남은 객체들은 오래 살아남을 것이고 따라서 가비지 컬렉션이 호출되는 빈도가 급격히 줄어들 것이다. 덕분에 어마무시한 성능을 얻을 수 있다.

자바도 공식적으로는 Young Generation과 Old Generation 두 개의 세대를 운영하지만, 실제로는 Young Generation이 세 개의 영역으로 세분화되어 있다.
 * 에덴 공간: 첫번째 세대.
 * Survivor 0: 첫번째 세대를 살아남은 세대.
 * Survivor 1: 역시 첫번째 세대를 살아남은 세대.

에덴 공간에서 살아남은 객체들이 Survivor 0과 1 세대를 번갈아 이동하고 나중에 오래 살아남은 애들은 Old Generation으로 가게 된다.

### Minor Heap
Youngest Heap, Bump Pointer Collection

### Major Heap
Old Heap, Mark & Sweep Collection

### Write (Read) Barrier
Generational을 도입하면 발생하는 문제를 해결하기 위해서 포인터 쓰기 연산에 도입되는 condition check. 컴파일러가 도와줘야 됨. Incremental에서 쓰이던 Barrier 기법이 그대로 적용되어서 같은 이름이 붙었고 요즘은 Generational에서 발생하는 문제가 더 커서 generational barrier가 좀더 유명함. 메이저 힙에서 마이너 힙으로 가는 포인터를 기록함.

여러 세대로 나눠진 경우, 세대가 다른 객체끼리 참조하게 되면 문제가 생긴다. 그래서 (특히 포인터를) 읽거나 쓰는 작업을 그냥 하면 안되고 이게 세대를 넘어서 이뤄지는 작업인지를 확인해야 한다. 이렇게 세대 간의 참조를 추적하기 위한 방법이 바로 쓰기 장벽 혹은 읽기 장벽이다.

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
## 존 매커시의 생각
1959년 존 매커시가 LISP에 가비지 컬렉션을 구현했을 당시 하드웨어 환경은 지금과 비교하면 엄청나게 열악했다. 메모리가 32KB 수준이었다. MB도 아니고 KB다. 그래서 당시 LISP의 가비지 컬렉션은 상당히 느린 편이었고, 존 매커시도 약간 임시 방편같은 느낌으로 생각했다고 한다. 시간이 지나면 연구자와 엔지니어들이 더 나은 방법을 찾을 것이라고 믿었던 것이다. 하지만 60년도 더 지난 지금, 오히려 많은 현대의 프로그래밍 언어에서 가비지 컬렉션은 핵심 기능으로 자리 잡은 사실이 재밌다.

## 가비지 컬렉션을 위한 하드웨어
가비지 컬렉션은 1959년에 LISP 프로그래밍 언어에 도입된 만큼 굉장히 오랜 세월 여러가지 언어에서 연구되고 개발되어 왔다. 그러다보니 정말 다양한 접근이 시도되었는데 그 중 하나는 바로 가비지 컬렉션을 위한 특수 하드웨어가 있었다는 점이다. 1980년대에 있었던 특수 목적 컴퓨터인 Symbolics나 TI Explorer는 "LISP 머신"(진짜 기계)였는데, 트레이싱 컬렉션의 쓰기 배리어 연산을 효율적으로 하기 위한 특수 하드웨어 연산이 지원되는 전용 FPGA가 달려있었다. 그래서 메모리 쓰기 연산이 발생하면 자동으로 쓰기 배리어 로직을 적용해서 기록했다고 한다.

당시에는 이런 특수한 하드웨어가 인공지능 연구에 필수적이라고 생각했었지만 이후에 PC의 성능이 급격하게 좋아지면서 경제성이 안나와서 금방 단종되었다고 한다.

## Duality

사실 레퍼런스 카운팅이랑 트레이싱 컬렉션은 수학적으로 듀얼이다!

수학에는 듀얼이라는 개념이 있다 (Duality). 나는 수학은 잘 모르기 때문에 이걸 정확하게 설명할 자신은 없어서 클로드에게 물어봤다. 일단 Duality는 개념, 정리, 수학적 구조를 다른 개념, 정리, 구조로 일대일 대응시키는 원리인데, 핵심은 다음 세 가지다.
 1. 어떤 변환을 두 번 적용하면 원래 것으로 돌아온다. (Involution)
 2. 두 개념이 대칭적인 관계를 가지며 하나의 관점에서 성립하는 것이 다른 관점에서도 대응되는 형태로 성립한다.
 3. 단순히 같은 것이 아니라 역 또는 보안 관계에 있는 개념들의 쌍이다.

이 관점에서 레퍼런스 카운팅과 트레이싱 컬렉션을 다시 바라볼 수 있다.
 * 트레이싱 컬렉션: 루트 집합에서 부터 시작해서, 살아있는 객체 (Live Object)를 추적한다.
 * 레퍼런스 카운팅: 안티-루트 집합(즉, 루트 집합이 아닌 모든 객체들)에서 부터 시작해서, 죽은 객체 (Dead Object, 즉 가비지)를 추적한다.

트레이싱 컬렉션은 "무엇이 여전히 쓰이고 있는지"를 추적하는 것이고, 레퍼런스 카운팅은 "무엇이 더이상 안쓰이는지"를 추적하는 것이다. 좀더 구체적인 각 컬렉션의 듀얼리티에 대한 수학적인 증명은 [A Unified Theory of Garbage Collection](https://web.eecs.umich.edu/~weimerw/2008-415/reading/bacon-garbage.pdf) by David F. Bacon et. al (IBM Watson)에 자세히 나와있다.

## 비용
여전히 풀리지 않은 문제다. 가비지 컬렉션 자체의 비용을 측정하는 것은 엄청나게 어렵다. 당장 같은 언어로 구현된 서로 다른 알고리즘을 비교하는 것도 어려운 문제인데. 수동으로 메모리를 관리하는 언어와 가비지 컬렉션 언어를 비교하는 것은 너무나도 방해하는 요소들 (Confounding Factors)가 많다. 당장 C언어와 OCaml을 비교한다고 치면,
 * 메모리 레이아웃: 논리적으로 같은 데이터 구조를 표현하더라도, 언어마다 데이터를 표현하는 메모리 레이아웃이 다르다. C에서는 64비트 정수가 곧바로 표현되지만 OCaml에서는 박싱된 정수가 기본으로 쓰이고 (Boxed Integer), 구조체나 struct로 들어가면 차이는 더욱 심각해진다. 이로 인해서 캐시 지역성에서 차이가 나게 되어서 성능 차이를 가린다.
 * 배열 바운드 체크: OCaml은 모든 배열 연산에 기본적으로 바운드 체크를 한다 (진짜인가?)
 * 함수 호출: C는 표준적인 함수 호출 컨벤션을 따르는 반면, 함수형 언어인 OCaml에서는 클로저가 오버헤드가 있다.
 * 컴파일러 최적화: 수십년간 수많은 엔지니어와 연구자들이 최적화한 GCC/Clang에 비해서 OCaml의 최적화는 부족한 부분이 있을 수 있다.
 * Write Barrier 오버헤드: OCaml의 Generational GC를 위해서 Write Barrier는 p필수인데, 이 오버헤드는 GC 시간 측정에 포함되지 않는다.
 * 메모리 할당자: OCaml은 GC의 할당자를 쓸 수 밖에 없지만, C에서는 다양하게 최적화된 할당자들이 많다. tcmalloc, jemalloc 등. 이 중에 어떤 걸 써야 공정한 비교일까?
 * 가비지 컬렉션 자체의 튜닝 파라미터: 가장 유명한 GC 언어인 Java의 경우, "너한테 할당된 메모리 용량은 최대 이만큼임" 정도의 튜닝만이 가능하다. 그래서 메모리를 약간 낭비하면서 속도를 가져가려는 경향이 있다고 한다. 반면 OCaml의 경우는 "실제로 써야하는 메모리보다 최대 이만큼 정도만 낭비하도록 하세요" 느낌의 튜닝이 가능하고, 이를 Space Overhead 라고 한다. 즉, 실제로 메모리 할당이 100GB를 했고, 20%의 공간 오버헤드를 파라미터로 갖고 있다면, 최대 120GB 만큼의 메모리만 사용하도록 GC가 열심히 일할 것이다.

그러니까 공정한 비교라는 것은 애초에 불가능한 것일지도 모른다.

---

글을 적는데 참고한 것들.
 - [Uniprocessor Garbage Collection Techniques](https://www.cs.cmu.edu/~fp/courses/15411-f08/misc/wilson94-gc.pdf) by Paul R. Wilson (CMU)
 - [Generation Scavenging: A Non-disruptive High Performance Storage Reclamation Algorithm](https://people.cs.umass.edu/~emery/classes/cmpsci691s-fall2004/papers/p157-ungar.pdf) by David Ungar
 - [A Unified Theory of Garbage Collection](https://web.eecs.umich.edu/~weimerw/2008-415/reading/bacon-garbage.pdf) by David F. Bacon et. al (IBM Watson)
 - [GC FAG -- draft](https://iecc.com/gclist/GC-faq.html)
 - [MemFix: Static Analysis-Based Repair of Memory Deallocation Errors for C](https://prl.korea.ac.kr/papers/fse18.pdf)

---

[^5]: 사실 이 문제는 마크 스윕에만 한정된 문제는 아니고 대부분의 힙 관리 방법에 공통된 문제다.
