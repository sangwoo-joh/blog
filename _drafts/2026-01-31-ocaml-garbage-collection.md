---
layout: post
published: true
tag: [dev, ocaml, essay]
title: OCaml의 가비지 컬렉션 이야기
---

## 목차
{:.no_toc}

* Table of contents
{:toc}

[가비지 컬렉션 이야기](../garbage-collection)에서 얘기했던 트레이싱 컬렉션이 현실의 프로그래밍 언어에서 어떻게 구현되어있는지를 OCaml 4.14 버전을 기준으로 뜯어보려고 한다. 참고로 OCaml 5.xx 부터는 GIL이 사라지고 이론과 연구와 엔지니어링이 뒷받침된 진정한 의미의 멀티코어 가비지 컬렉션이 도입되었는데, 이건 또 다른 엑스트라 라지 포스팅이 필요한 이야기라 뒤로 미루고, 일단은 GIL이 있는 싱글코어 가비지 컬렉션을 기준으로 살펴보기 위해서 4.xx의 최신 버전인 4.14를 골랐다.


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

---

글을 적는데 참고한 것들.
 - [Memory Management](https://signalsandthreads.com/memory-management/) with Stephen Dolan (Jane Street)
 - [OCaml 4.14.2](https://github.com/ocaml/ocaml/tree/4.14) Source Code
 - [The Saga of Multicore OCaml](https://youtu.be/XGGSPpk1IB0)
