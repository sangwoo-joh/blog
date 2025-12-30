---
layout: post
tags: [ocaml]
published: true
title: OCaml로 PS 하기 -5-
subtitle: OCamlgraph 흉내내기
---

최애 언어 [OCaml](https://ocaml.org/) 로 문제를 풀어보자 다섯 번째 시리즈다.


### 그래프
그래프는 노드의 집합 $$V$$와 엣지의 집합 $$E$$로 구성된다. 이건 이론적인 내용이고, 실제 문제 풀이에서는 "두 노드 사이에 엣지가 있느냐?" 가 주된 관심사이다. 그래서 C 계열 언어로 코드를 짤 때는 주로 2차원 인접 배열로 그래프를 구현한다.

그럼 최애 언어 OCaml 에서는 어떻게 그래프를 모델링할 수 있을까? 답은 [OCamlgraph](http://ocamlgraph.lri.fr/doc/)에서 찾을 수 있었다.

OCamlgraph에는 두 가지 타입의 그래프가 있다: 하나는 Persistent이고 다른 하나는 Imperative이다. Persistent는 그래프가 immutable 타입이 되어 함수형에 적합하고, Imperative는 그래프가 reference 타입이 되어 사이드 이펙트를 통해서 그래프를 조작해야 한다. 코드를 보면 Persistent는 [Map으로 구현](https://github.com/backtracking/ocamlgraph/blob/master/src/persistent.ml#L43) 되어 있고, Imperative는 [Hashtbl로 구현](https://github.com/backtracking/ocamlgraph/blob/master/src/imperative.ml#L44) 되어 있다.

그럼 이제 이걸 흉내내서 문제를 풀어보자.


#### [트리 - 리프 노드 개수 세기](https://www.acmicpc.net/problem/1068)
백준에서 "그래프 이론"으로 분류된 문제 중 기초적인 문제를 하나 골라왔다. 제목은 트리이지만 실제로 트리는 그래프의 특수한 형태 (싸이클이 없는) 이므로 상관없다.

이 문제는 OCamlgraph의 Persistent를 흉내내서 풀어보았다. 우선, 그래프는 "노드에서 (연결된) 노드 집합으로 가는 함수"로 정의할 수 있다.

이를 위해 노드를 먼저 정의하자. 문제를 보면 노드는 그냥 정수형이다. 하지만 OCaml에서 집합이나 맵 펑터를 이용하려면, 이를 모듈로 정의할 필요가 있다. 집합과 맵 펑터 모두 모듈 시그니쳐로 [비교할 수 있는 타입](http://caml.inria.fr/pub/docs/manual-ocaml-4.07/libref/Set.OrderedType.html)을 요구한다.

```ocaml
module Node = struct
  type t = int

  let compare = Stdlib.compare
end
```

이 노드 모듈로 노드의 집합과 노드의 맵을 정의할 수 있다.

```ocaml
module NodeSet = Set.Make (Node)
module NodeMap = Map.Make (Node)
```

이로부터 트리, 즉 (싸이클이 없는) 단방향 그래프 모듈을 만들어보자. 어떤 인터페이스가 필요할까? 문제를 풀기 위해서는 아래와 같은 인터페이스가 필요함을 알 수 있다.
  - 노드 하나를 추가/삭제하는 함수 `add_vertex`
  - 두 노드를 잇는 엣지를 추가하는 함수 `add_edge`
  - 어떤 노드가 리프 노드인지를 확인하는 함수 `is_leaf`
  - 그래프 전체를 탐색하기 위한 모듈

모듈 이름은 적당히 `Digraph`로 하고, 위의 인터페이스들을 하나씩 차근차근 만들어보자.

```ocaml
module Digraph = struct
  module S = NodeSet
  module M = NodeMap

```

먼저 그래프 모듈 안에서 집합과 맵 연산을 자주 사용할 것 같으니 짧은 모듈 별칭을 지어주자.

```ocaml
  type t = S.t M.t
```

그래프의 타입은 앞서 말한것 처럼 노드에서 노드의 집합으로 가는 함수 (맵) 이 된다.

```ocaml
  let empty : t = M.empty
```

그래프를 조작하기 위해서는 반드시 빈 그래프가 필요하다. 이 빈 그래프로부터 그래프 연산을 수행해서 새로운 그래프를 만들어야 하기 때문이다. 그래프 타입에 따라 이는 단순히 비어있는 노드 맵이다.

```ocaml
  let mem_vertex g v = M.mem v g

  let mem_edge g v1 v2 = try S.mem v2 (M.find v1 g) with Not_found -> false
```

노드를 추가/삭제하는 함수를 만들기 전에, 노드/엣지가 그래프에 있는지 확인하는 멤버 함수를 만들었다. 노드 멤버 함수는 맵에 있는지만 확인하면 되고, 엣지 멤버 함수는 (1) 일단 소스 노드를 가지고 맵을 뒤진 뒤에 (2) 맵에 있는 싱크 노드 집합 안에 싱크 노드가 포함되는지를 보면 된다.

```ocaml
  let add_vertex g v = if mem_vertex g v then g else M.add v S.empty g
```

노드 하나만 추가하는 함수를 구현했다. 앞서 만든 노드 멤버 함수를 이용해, 노드가 이미 있으면 원래 그래프를 리턴한다. 없으면 그때 추가하는데, 여기서 노드 하나만 추가하는 것은 곧 해당 노드와 연결된 노드 집합이 없다는 것을 의미한다. 따라서 빈 노드 집합과 맵핑 시켜준다.

```ocaml
  let unsafe_add_edge g v1 v2 = M.add v1 (S.add v2 (M.find v1 g)) g

  let add_edge g v1 v2 =
    if mem_edge g v1 v2 then g
    else
      let g = add_vertex g v1 in
      let g = add_vertex g v2 in
      unsafe_add_edge g v1 v2
```

엣지를 추가하는 함수는 조금 복잡하다. 우선 런타임 예외가 발생할 수 있는 Unsafe 함수를 만들었다. 이 함수는 `v1`에 맵핑된 싱크 노드 집합에 `v2`를 추가하는데, 싱크 노드 집합을 못 찾으면 `Not_found` 예외를 일으킨다. 하지만 실제 사용할 `add_edge` 함수 안에서 이런 경우가 없도록 잘 처리했으니 괜찮다.

```ocaml
  let remove_vertex g v =
    if mem_vertex g v then
      let g = M.remove v g in
      M.fold (fun k s -> M.add k (S.remove v s)) g empty
    else g
```

노드를 하나 제거하는 함수는 다음과 같이 구현할 수 있다. 일단 멤버 함수를 이용해 노드가 없는 경우는 그냥 원래 그래프를 돌려준다. 있으면, 일단 맵에서 그 노드를 삭제한다. 그리고 맵 전체를 돌면서, 모든 싱크 노드 집합에서 해당 노드를 삭제한다. Persistent한 스타일로, 맵 전체를 fold 하면서 기존의 노드 집합에서 해당 노드를 삭제하여 새로운 맵에 추가하도록 했다. 이때 초기값은 빈 그래프 (빈 맵) 이다. 이 기발한 방법은 Ocamlgraph의 [Persistent 코드](https://github.com/backtracking/ocamlgraph/blob/master/src/persistent.ml#L69)를 참조했다.

```ocaml
  let is_leaf g v = try S.is_empty (M.find v g) with Not_found -> false
```

노드와 연결된 노드 집합이 공집합이면 해당 노드는 리프 노드이다.

여기까지 그래프를 조작하는 인터페이스를 만들었다. 그러면 그래프를 탐색하는 모듈은 어떻게 만들면 좋을까? 역시 OCamlgraph에서 힌트를 얻을 수 있었는데, [Traverse](http://ocamlgraph.lri.fr/doc/Traverse.html)라는 모듈이 제공하는 펑터를 이용해 각 그래프마다 원하는 탐색, 즉 넓이 우선 탐색이나 깊이 우선 탐색을 위한 모듈을 만들 수 있다. 그리고 각 탐색마다 fold, iter등의 조작 옵션을 통해 원하는 걸 얻을 수 있게끔 해뒀다. 깔끔한 인터페이스다.

문제를 풀기 위해서 모든 탐색 방법과 모든 조작 옵션이 필요하진 않다. 여기서는 단순하게 DFS를 이용한 fold 를 구현하면 리프 노드의 개수를 셀 수 있을 것이다.

```ocaml
module Dfs (G: module type of Digraph) = struct
  module H = Hashtbl

  let fold ~f ~init ~g ~root =
    let explored = H.create 50 in
    let frontier = Stack.create () in
    let push v =
      if not (H.mem explored v) then (
        H.add explored v () ;
        Stack.push v frontier )
    in
    let rec loop acc =
      if Stack.is_empty frontier then acc
      else
        let visit = Stack.pop frontier in
        let acc = f visit acc in
        G.iter_succ g ~f:push ~src:visit ;
        loop acc
    in
    push root ;
    loop init
end
```

DFS `fold`는 다음과 같이 만들 수 있다. 일단 DFS 자체는 우리가 만든 (싸이클 없는 단방향) 그래프를 받아서 깊이 우선 탐색을 하는 모듈을 만드는 펑터가 된다. `fold` 는 네 가지 입력을 받는데 (1) 각 노드마다 fold 할 함수, (2) fold 초기값, (3) 그래프, (4) 탐색을 시작할 루트 노드이다. 그리고 이를 이용해 단순히 Stack을 활용한 깊이 우선 탐색을 구현하면 된다.

다만 한 가지, 이를 위해 추가적으로 필요한 그래프 인터페이스가 있다. 바로 어떤 소스 노드에 연결된 싱크 노드 집합 전체에 함수를 적용하는 함수이다. 여기서는 다음 탐색을 위해 스택에 넣는 함수 `push`를 적용해야 하기 때문에, fold나 map이 아닌 iter가 필요하다. 이를 `Digraph` 모듈에 구현하면 다음과 같다.

```ocaml
  ...
  let iter_succ g ~f ~src = try S.iter f (M.find src g) with Not_found -> ()
  ...
```

이제 이렇게 만든 그래프 모듈을 이용해서 그래프의 리프 노드 개수를 세는 함수를 다음과 같이 만들 수 있다.

```ocaml
let count_leaves g root =
  if Digraph.mem_vertex g root then
    let module DFS = Dfs (Digraph) in
    DFS.fold
      ~f:(fun node count -> if Digraph.is_leaf g node then succ count else count)
      ~init:0 ~g ~root
  else 0
```

루트 노드가 그래프에 없으면 당연히 리프 개수는 0이다. 있으면, 탐색을 위한 DFS 모듈을 만들고, 리프 여부를 판단하여 개수를 누적하는 함수를 그래프 전체에 fold 한다.

나머지는 입력을 받아 그래프를 적절히 만들어서 `count_leaves` 함수에 적용하기만 하면 된다. 이렇게 4ms 의 솔루션을 얻었다. 하하.

#### [그래프 - BFS와 DFS](https://www.acmicpc.net/problem/1260)
이참에 그래프 탐색을 다 완성시켜보자. 마침 문제 제목부터 대놓고 BFS와 DFS인게 있어서 이것도 풀어봤다.

이 문제는 앞의 트리와 다르게 양방향 그래프이다. 그러므로 엣지를 추가할 때 양방향으로만 적절히 추가해주면 될 것이다. 그리고 똑같이 풀면 재미없으니 이번에는 그래프 타입을 해시 테이블로 바꿔보자.

Hashtbl 펑터를 이용하려면 앞의 노드 모듈에 해싱을 위해 [추가적인 값](http://caml.inria.fr/pub/docs/manual-ocaml-4.07/libref/Hashtbl.HashedType.html)이 더 필요하다: `hash`와 `equal`을 구현해주면 된다.

```ocaml
module Node = struct
  type t = int

  let compare = Stdlib.compare

  let equal = Stdlib.( = )

  let hash = Hashtbl.hash
end

module NodeSet = Set.Make (Node)
module NodeHashtbl = Hashtbl.Make (Node)
```

이제 이걸로 양방향 그래프 Bigraph 모듈을 만들어보자.

```ocaml
module Bigraph = struct
  module S = NodeSet
  module H = NodeHashtbl

  type t = S.t H.t

  let empty : t = H.create 1000

  let mem_vertex g v = H.mem g v

  let mem_edge g v1 v2 = try S.mem v2 (H.find g v1) with Not_found -> false

  let add_vertex g v = if mem_vertex g v then () else H.add g v S.empty

  let unsafe_add_edge g v1 v2 = H.replace g v1 (S.add v2 (H.find g v1))

  let add_edge g v1 v2 =
    if mem_edge g v1 v2 then ()
    else (
      add_vertex g v1 ;
      add_vertex g v2 ;
      unsafe_add_edge g v1 v2 ;
      unsafe_add_edge g v2 v1 )

  let iter_succ g ~f ~src = try S.iter f (H.find g src) with Not_found -> ()
end
```

Hashtbl은 Imperative 타입이기 때문에 사이드 이펙트를 이용해서 그래프 (노드 집합으로 가는 노드 테이블)을 조작한다. 따라서 빈 그래프를 만드는 `empty`를 제외한 나머지 조작 함수들은 모두 리턴 타입이 `()` 이다. 그 외에 Hashtbl 문서를 잘 읽어보면, 같은 키 값으로 `add` 함수를 여러번 호출하면 이전의 값이 지워지는게 아니라 *가려지기* 때문에, 만약 같은 키 값으로 여러번 다른 데이터를 추가한 뒤에 해당 키 값을 한번 삭제하면 마지막 바로 직전의 키-값 맵핑이 부활한다. 따라서 엣지를 추가할 때 `H.add`가 아니라 `H.replace`를 호출해야 한다. 사실 이 문제에서는 노드를 삭제하는 경우가 없어서 크게 문제는 안되지만 덕분에 표준 라이브러리가 어떻게 동작하는지 이번 기회에 더 잘 알게 되었다.

이제 이 양방향 그래프 모듈로부터 각각 깊이 우선 탐색 / 넓이 우선 탐색을 수행할 수 있는 탐색용 펑터를 만들어보자. 이 문제에서는 단순히 탐색하는 순서대로 노드 번호를 출력하라고만 되어 있으니 이번에는 fold가 아니라 iter가 있으면 될 것이다.

```ocaml
module Dfs (G: module type of Bigraph) = struct
  module H = Hashtbl

  let iter ~f ~g ~root =
    let explored = H.create 2048 in
    let rec loop v =
      if not (H.mem explored v) then
        H.add explored v () ;
        f v ;
        G.iter_succ g ~f:loop ~src:v )
    in
    loop root
end

module Bfs (G: module type of Bigraph) = struct
  module H = Hashtbl

  let iter ~f ~g ~root =
    let explored = H.create 2048 in
    let frontier = Queue.create () in
    let push v =
      if not (H.mem explored v) then (
        Queue.push v frontier ;
        H.add explored v () )
    in
    let rec loop () =
      if Queue.is_empty frontier then ()
      else
        let v = Queue.pop frontier in
        f v ;
        G.iter_succ g ~f:push ~src:v ;
        loop ()
    in
    push root ;
    loop ()
end
```

문제의 조건에 따라 fold가 아닌 iter를 구현해야 하는데, 각 탐색마다 까다로웠던 부분이 하나 씩 있었다.

먼저 DFS를 보자. 문제에서 "방문할 수 있는 정점이 여러 개인 경우에는 **정점 번호가 작은 것**을 먼저 방문하고, ..."라고 명시하고 있다. 만약 이전 트리 문제처럼 스택을 이용해서 DFS를 구현했다면, 이 조건을 지키기가 까다롭다. 왜냐하면, 우리가 구현한 `iter_succ`, 즉 인접한 싱크 노드 집합에 대해 함수 f를 적용하는 함수는 내부적으로 [`Set.iter`](http://caml.inria.fr/pub/docs/manual-ocaml-4.07/libref/Set.Make.html)를 이용하고 있고, 당연히 이 함수는 집합의 원소가 *증가하는 순서대로* f를 적용한다. 그래서 다음 방문 노드를 `iter_succ` 과 스택을 이용해서 처리하게 되면 스택의 특성으로 인해 작은 것부터 스택에 들어가게 되고 결과적으로 **정점 번호가 큰 것**을 먼저 방문하게 된다. 그래서 `Dfs.iter` 에서는 스택을 사용하지 않고 일반적인 재귀함수를 이용해서 방문 순서를 지키도록 했다.

BFS에서는 다음 방문할 노드를 큐 (frontier) 에 쌓으면 되는데, "이 노드를 예전에 방문했었나?"를 이 큐에 넣기 전에 확인해야 한다. 이거만 지키면 나머지는 자명하다.

나머지 부분은 역시 입력으로부터 그래프를 만들고, 적절히 출력하기만 하면 된다. 덕분에 76ms의 솔루션을 얻었다. 다른 C++ 솔루션들을 보니 4ms (...) 투성이라 조금 아쉽긴 하지만, 최애 언어로 문제 풀이가 잘 동작하는 걸 지켜보는 뿌듯함이 더 크다.


#### 다섯 번째 시리즈를 마무리하면서...
최애 언어로 문제 풀이 시리즈가 벌써 다섯 번째다. 업무에서 최애 언어를 쓰지 못하는 아쉬움에 몸부림 치면서 시작한 시리즈가 여기까지 오게 될 줄은 몰랐다. 감개가 무량하다.

시리즈를 진행하면서 놀라웠던 점은 의외로 OCaml이 문제를 풀기에 괜찮은 언어라는 것이다. 물론 수행 시간은 C++나 Rust에 비해서는 조금 아쉽지만 (얘넨 무슨 4ms, 8ms 이런다...), 다른 GC 언어에 비하면 오히려 **월등하다**. 자바는 대부분 300ms가 넘어가고, 파이썬은 500ms, 1000ms 이런다. 거기다 언어 자체가 간결하며, 모듈을 이용해서 깔끔한 추상화가 가능하고, 의외로 Stdlib 표준 라이브러리도 나쁘지 않으며, functional과 imperative를 적절히 취사선택할 수 있고, 무엇보다 **타입 안전** 해서 런타임 예외가 어디서 발생할지 짐작하기 쉽다.

이 시리즈가 어디까지 갈 진 모르겠지만 당분간 계속 해볼 예정이다.
