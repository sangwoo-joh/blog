---
layout: post
tags: [ocaml]
published: true
title: OCaml로 PS 하기 -3-
subtitle: 내 친구 ADT
---

최애 언어 [OCaml](https://ocaml.org/) 로 문제를 풀어보자 세 번째 시리즈다.


#### 근황
마지막 포스트가 8/27 이었으니 대략 2주만의 포스팅이다. 변명을 하자면 그간 조금 바빴다. 나도 먹고 살아야지 별 수 있나.

한국 기업들의 채용 빅 이벤트 중 하나인 하반기 공개 채용을 위해 캠퍼스 리크루팅에 다녀왔다. 이거 때문에 예비군도 미뤘다. 벌써 두 번이나 미뤘기 때문에 다음 번 2차 보충 훈련 마저 참여하지 못하면 형사고발 당하여 이틀 구류 당할 수 있단다. 법치주의를 얕보지 말자.

리크루팅 참여로 발생하는 약 1주일간의 부재를 위해 야근도 했다. 일정을 못지키면 나만 손해기 때문에 '언제까지 하겠다'고 한 일은 되도록 지키고자 한다. 사실 그렇다고 엄청나게 야근을 한 것은 아니다. 세상이 조금씩 진일보 하고 있기 때문에 엄청나게 야근을 하고 싶어도 할 수가 없기도 하다. 다만 집에 와서 씻고 잠들기 까지의 대략 1 ~ 2 시간에 피씨(혹은 노트북)을 켜서 글을 쓰고자 하는 의지가 없었을 뿐이다. 맨날 반성하는 것 같은데 또 반성한다. 인생은 반성의 연속이다. 뭐든 깨닫고 과거보다 A4지 한 장 정도의 두께만큼 더 좋은 사람이 되도록 노력하자. 그러면 언젠가는 책 한 권 만큼은 좋은 사람이 되어 있지 않을까?

포스팅을 쓰기 위해서는 몇 가지 준비가 필요한 법인데, 그 중 하나가 바로 심신의 안정을 위한 주변 청소다. 책상 청소로 시작했다 결국 온 집안 대 청소를 하였고 그러고도 시간이 남아돌아 결국 이렇게 포스팅을 한다. 그래도 좋은 점은 있다. 덕분에 예전 연구실에서 쓰던 씽크패드 빨콩 무선 키보드를 찾았다! 지금 이 포스팅도 이 키보드로 작성하고 있다.

뱀발로 당분간은 계속 쉬운 문제들만 풀 것 같다. 예전 C/C++ 로 풀었던 문제들을 최애 언어로 다시 풀어보는 수준의 취미생활이기 때문이다.

그럼 각설하고 문제를 풀어보자.


### [1991번: 트리 순회](https://www.acmicpc.net/problem/1991)
좋은 문제이다. 잘 구성된 트리가 있으면 그냥 전위/중위/후위 순회 한 결과를 출력하기만 하면 된다! 최애 언어의 자랑 중 하나인 ADT를 이용해서 재귀적 데이터 구조를 만들면 정말 쉽고 아름답게 풀릴 것만 같은 문제다. 참고로 ADT는 Abstract Data Type이 아니다. [Algebraic Data Type](https://en.wikipedia.org/wiki/Algebraic_data_type)이다. 헷갈리지 말자.

일단 입력을 어떻게 받을지는 제쳐두고 타입부터 적어보자. 뭔가 드디어 최애 언어 다운 코드가 나오는 것 같아서 설렌다.

```ocaml
type tree = Node of (tree * char * tree) | Nil
```

아름답다. 합 타입으로 트리 전체를 정의하면서 곱 타입으로 노드를 정의했다. 노드는 왼쪽/오른쪽 자식으로 `tree` 스스로를 가지도록 해서 트리의 재귀적인 성질을 잘 나타내었다. [`Nil`](https://en.wikipedia.org/wiki/Nil#Computing)은 그냥 널이랑 같은 거다. 왠지 모르게 함수형 언어에서 자주 쓰이는 관용적인 널 이길래 괜히 친근한 척 좀 해봤다.

이제 이 트리를 순회하는 함수를 짜면 되는데, 세 종류를 각각 따로 짜고 싶진 않다. 어차피 재귀적으로 방문하는 것은 똑같고 노드를 언제 방문할지만 달라지기 때문에 그냥 함수 하나로 퉁치자. 대신 어떤 순서일지만 파라미터로 받자.

```ocaml
type order = Preorder | Inorder | Postorder

let rec traverse ~order ~visit tree =
  let traverse' = traverse ~order ~visit in
  match tree with
  | Nil -> ()
  | Node (left, value, right) -> (
    match order with
    | Preorder -> visit value ; traverse' left ; traverse' right
    | Inorder -> traverse' left ; visit value ; traverse' right
    | Postorder -> traverse' left ; traverse' right ; visit value )
```

일단 순회 순서를 위한 `order` 타입을 정의했다. 그리고 `traverse` 함수에서 이 `order` 를 파라미터로 받아서 실제 노드를 방문할 때 순서에 맞게 처리한다. 실제 방문을 위해서는 노드가 담고 있는 값을 받아서 `()`를 내놓는 함수 `visit`을 넘겨주면 된다. 이 문제에서는 그냥 `char` 값을 출력하면 될 듯. 그리고 방문 순서에 상관없이 같은 순서와 `visit` 함수를 가지고 재귀적으로 각 노드의 왼쪽/오른쪽 자식을 방문해야 하기 때문에, 미리 이 부분을 `traverse'` 클로저로 만들어 두었다. 각 순서별 방문은 너무 뻔하기 때문에 생략한다.

여기까지 최애 언어로 (내 기준) 러블리하게 짤 수 있는 부분이다. 이제 남은 일은 현실 세계의 입력을 다루는 일이다.

일단 문제를 잘 읽어보면 노드 개수가 26개, 즉 알파벳 수 만큼임을 알 수 있다. 그 외에 루트 노드가 항상 `A` 인 것을 제외하면 입력이 들어오는 순서에 제약이 없다. 그래서 C/C++에서 했던 것처럼, 입력을 받자마자 노드가 가리키는 자식 포인터를 업데이트하면서 곧바로 트리를 구성하는 방식은 힘들 것 같다. 그러니 우선은 입력을 전부 받아서 배열에 저장해뒀다가, (우리는 루트 노드가 어딘지 아니까) 루트 노드부터 시작해서 탑 다운으로 구성하는 방식을 써보자.

일단 입력을 받아서 크기 26의 배열에 저장하는 함수를 짜보자. 자식 두 개에 대한 정보를 담아야 하는데 굳이 타입을 선언하기 보다는 그냥 튜플로 담으면 될 것이다.

```ocaml
let to_idx ch = int_of_char ch - int_of_char 'A'

let read_input total () =
  let node_info = Array.make 26 (' ', ' ') in
  for i = 0 to total - 1 do
    Scanf.scanf " %c %c %c" (fun root left right ->
        node_info.(to_idx root) <- (left, right) )
  done ;
  node_info
```

다른건 다 제쳐두고, 여기서 가장 중요한 부분이 바로 `Scanf` 부분에 있다. 입력을 받을 때 반드시 위의 코드 처럼 `" %c %c %c"` 형태로 받아야 한다. 첫 번째 `%c` 앞에 공백이 없으면 **런타임 에러가 뜬다**. 이거 때문에 또 한참을 헤매었다. 저 공백이 없으면 이전 줄의 줄바꿈 문자(LF; Line feed)도 캐릭터 버퍼로 스캔해서 배열 인덱스를 초과하기 때문이다.

이렇게 입력을 전부 받아서 `(char * char) array` 를 만들었다. 이제 루트 노드가 항상 `A` 라는 사실을 이용해서 트리를 구성해보자.

```ocaml
let construct_tree node_info =
  let rec construct c =
    match node_info.(to_idx c) with
    | '.', '.' -> Node (Nil, c, Nil)
    | l, '.' -> Node (construct l, c, Nil)
    | '.', r -> Node (Nil, c, construct r)
    | l, r -> Node (construct l, c, construct r)
  in
  construct 'A'
```

`A` 부터 시작해서 배열에 자식 노드를 찾아서 패턴 매칭을 통해 어떤 값인지에 따라 적절히 트리를 구성할 뿐이다. 어려운 것은 없다.

이제 마지막으로 노드 개수를 입력으로 받아서 트리를 구성하고, 각 순서별로 트리를 순회하여 문제를 푸는 메인 진입점을 짜면 완성이다.

```ocaml
let solve () =
  let visit c = print_char c in
  Scanf.scanf "%d" (fun total ->
      let node_info = read_input total () in
      let tree = construct_tree node_info in
      traverse ~order:Preorder ~visit tree ;
      print_newline () ;
      traverse ~order:Inorder ~visit tree ;
      print_newline () ;
      traverse ~order:Postorder ~visit tree ;
      print_newline () )

let () = solve ()
```

이렇게 하여 4ms 의 솔루션을 얻었다. 사실 처음 시작할 땐 OCaml로 입력을 어떻게 처리할지에 대한 고민 때문에 이렇게 시리즈가 이어질지 몰랐는데, 갈수록 최애 언어로 더 많은 어려운 문제를 풀 수 있을 것만 같은 예감이 든다. [이전 포스팅](https://blog.untyped.kr/restart)에 적어둔 깨달음대로 꾸준히 풀다보면, 누군가는 OCaml의 매력을 알고 함께 풀어가는 아름다운 세상이 오지 않을까? 하는 두루뭉실한 기대를 해본다.
