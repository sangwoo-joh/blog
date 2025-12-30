---
layout: post
tags: [ocaml]
published: true
title: OCaml로 PS 하기 -1-
subtitle: 힘내라 OCaml
---

최애 언어 [OCaml](https://ocaml.org/) 로 문제를 풀어보자.

[백준](https://www.acmicpc.net)은 ([나무위키](https://namu.wiki/w/Baekjoon%20OJ)에 따르면) 세계 최대 수준의 문제 수를 보유하고 있는 알고리즘 트레이닝 사이트이다. 문제가 많은 것뿐 아니라, 수많은 프로그래밍 언어를 지원한다고 한다.

과연 찾아보니 [지원하는 언어 목록](https://www.acmicpc.net/help/language)의 끝 무렵에서 OCaml 을 찾을 수 있었다. 오오 백준 오오. 다만 플레이스 홀더 링크를 지원하지 않아 직접 OCaml을 검색해야 한다(...). 거기다 왜 바로 아래에 `Brainfuck` 이 있는 것인지... 미묘한 위치 선정.

![boj-ocaml](/assets/img/boj-ocaml.png)

친절하게 컴파일 커맨드와 버전까지 명시되어 있다. 지원하는 컴파일러 버전은 글 작성일 기준 OCaml 4.07.0 이다. 오오. 나름 [작년 이맘때쯤](https://ocaml.org/releases/index.html) 릴리즈한 버전을 지원하는 걸 보니 꾸준히 업데이트 하는 듯 하다. 하지만 아무런 라이브러리를 쓸 수 없다는 점은 아쉽다. [OCamlgraph](http://ocamlgraph.lri.fr/index.en.html) 라이브러리 써서 그래프 문제 풀어보고 싶었는데. 아쉽. 우리 손엔 빌트인 라이브러리 뿐이다.

근데 컴파일 커맨드가 `ocamlc` 라니. PS의 주력 언어 중 하나인 C++의 경우 컴파일 커맨드가 아래와 같은데:

![boj-cpp](/assets/img/boj-cpp.png)

치사하게(?) 주력 언어만 최적화 옵션을 챙겨주는 것을 볼 수 있다. 우리 OCaml도 얼마든지 [네이티브 코드](http://caml.inria.fr/pub/docs/manual-ocaml-4.07/native.html) 컴파일 할 수 있고 함수형 최적화인 [Flambda](http://caml.inria.fr/pub/docs/manual-ocaml-4.07/flambda.html) 라는 친구도 있는데. OCaml 혐오를 멈춰주세요.

최적화는 차치하더라도 이런 사이트의 문제 풀이를 하려면 가장 큰 장벽이 입력을 처리하는 일이다. 대부분의 문제가 C/C++ 같은 언어를 대상으로 만들어지다보니 OCaml에게 불친절한 입력이 들어온다. `scanf` 를 염두에 두고 입력 개수를 먼저 받고 그 후 반복문을 돌아서 받는다던가, 특수한 값 (e.g. `-1`) 이 들어오기 전까지 계속 입력을 받아야 한다던가 하는. 마이너의 비애이지만 어쩔 수 없다. 몇 십년을 이어온 유구한 전통의 포맷이다. 우리가 맞춰야 한다.

다행히 OCaml은 명령형 프로그래밍을 아주 잘 지원하며, 언어 예제 소스에도 나와 있듯 표준 라이브러리에 있는 [Scanf](http://caml.inria.fr/pub/docs/manual-ocaml-4.07/libref/Scanf.html) 모듈을 잘 갖다 쓰면 충분히 가능할 것 같다.

그럼 실제로 문제를 한번 풀어보자.


### [1157번: 단어 공부](https://www.acmicpc.net/problem/1157)
예전에 C++로 풀었던 문제 중 입력 포맷이 간단한 놈으로 골라봤다. 문제를 설명하자면 길이 1,000,000 미만의 알파벳 문자열이 주어지면 대/소문자 구분 없이 알파벳의 빈도수를 계산해서 가장 많이 나온 친구를 찾아 대문자로 출력하는 문제다. 2개 이상일 경우는 `?`를 출력하란다.

이걸 C++로 풀었으면 아주 명령형으로 풀었을 것이다. `scanf`로 `char` 배열에 입력을 받아다가, 인덱스마다 돌면서 전부 대문자로 몰아서 크기 26짜리 배열에 `알파벳 - 'A'`를 인덱스로 하여 빈도수를 계산하고, 이렇게 구한 전체 빈도수에서 최대값을 구하여 두 개 이상이면 `?`를, 아니면 키가 되는 알파벳을 출력했겠지.

하지만 이번엔 함수형으로 접근할 것이다. 함수형 접근이 뭐냐고? 사실 나도 잘 모른다. 그냥 최애 언어를 업무에 써먹을 수 없는 슬픔에 몸부림 치는 것이니 넘어가자. 최적의 솔루션이 아닐 수 있으니 염두에 두자.


일단 앞서 말했듯 우리에겐 그저 OCaml 4.07.0 바이트코드 컴파일러 뿐이다. [Base](https://github.com/janestreet/base)도 Ocamlgraph도 없다. 표준 라이브러리로 모든 것을 해보자.

일단 `대문자 알파벳 -> 빈도수`로 가는 맵 모듈을 정의하자.

```ocaml
module CharFreq = Map.Make (Char)
```

표준 [`Map`](http://caml.inria.fr/pub/docs/manual-ocaml-4.07/libref/Map.Make.html) 모듈과 [`Char`](http://caml.inria.fr/pub/docs/manual-ocaml-4.07/libref/Char.html) 모듈을 이용하면 간단하다. 네이밍 센스가 구려서 `CharFreq`가 한계다.

이제 문자열을 받아서 이 모듈 타입, 정확히는 `int32 CharFreq.t` 타입을 내놓는 함수를 만들자. 문자열 길이가 1,000,000 미만이니 빈도수는 `int32` 타입이면 널널하다.

```ocaml
let make_map str =
  let char_seq = Seq.map Char.uppercase_ascii (String.to_seq str) in
  let update_cnt = function
    | None -> Some Int32.one
    | Some cnt -> Some (Int32.succ cnt)
  in
  Seq.fold_left
    (fun acc ch -> CharFreq.update ch update_cnt acc)
    CharFreq.empty char_seq
```

몰랐는데 4.07.0 부터 [`Seq`](http://caml.inria.fr/pub/docs/manual-ocaml-4.07/libref/Seq.html)가 [표준 라이브러리에 들어가있더라](https://ocaml.org/releases/4.07.0.html). 그래서 그걸 활용해보았다. 일단 `String.to_seq` 로 문자열을 알파벳의 시퀀스로 만들고 `Char.uppercase_ascii`로 전부 대문자로 만든다. 그 후 `Seq.fold_left`를 이용해서 정의한 `CharFreq` 타입의 맵을 만들면 된다.

이제 빈도수는 셌으니 그 중 제일 많이 나오는 친구를 찾는 함수를 만들자.

```ocaml
let find_max_freq_map map =
  let map_list = CharFreq.bindings map in
  let sorted_list =
    List.sort (fun x y -> Int32.compare (snd x) (snd y)) map_list
  in
  match List.rev sorted_list with
  | [] -> '?'
  | [one] -> fst one
  | one :: two :: _ ->
      if snd one = snd two then '?' else fst one
```

`Map.bindings` 함수로 맵 전체를 (`키 * 값`) 쌍의 연관 리스트로 뽑아낼 수 있다. 이 중 빈도수, 즉 `값`의 최대를 찾으면 되는데 귀찮으니 그냥 정렬하자. 어차피 최대값이 두 개 이상인 경우도 처리해야 하니 정렬이 편하다. 다만 생각없이 정렬해버리면 오름차순 정렬을 해버리니 결과 리스트를 뒤집던가 아니면 `-`를 줘서 내림차순으로 정렬하는 것이 편하다. 여기선 `List.rev` 로 뒤집어 봤다. 둘 다 해봤는데 큰 차이 없더라.

그 후 이 정렬된 리스트를 패턴매칭해서 원하는 형태의 정답을 계산하자. 일단 리스트가 비었으면 `?` 일 것이다 (딱히 명시되어 있진 않은데 왠지 그럴 것 같다). 하나만 있는 경우는 그게 바로 답이니 돌려주면 된다. 이미 맵을 만들 때부터 대문자로 만들었기 때문에 충분하다. 두 개 이상인 경우에는 앞의 두 개만 떼와서 빈도수를 비교해보고 같으면 `?`를, 아니면 첫 번째 알파벳을 돌려주면 된다.


이제 다 구현한 것 같다. 채점을 위해 입력값 처리를 해보자.

앞서 말한 `Scanf` 모듈을 이용하면 포맷별 입력을 받아 원하는 타입으로 받고 바로 함수를 적용할 수 있는듯 하다. 그래서 다음과 같이 짜봤다.

```ocaml
let solve () =
  let solve_helper str =
    let freq = make_map str in
    let answer = find_max_freq_map freq in
    print_char answer
  in
  Scanf.scanf "%s" solve_helper
```

OCaml 은 딱히 메인 진입점이 없기 때문에 이 `solve`를 호출해서 메인으로 동작하게 하면 될 것이다.

```ocaml
let () = solve ()
```

이제 제출해보자. 잘 통과한다. 다만 바이트코드 따리에 최적화도 없어서 메모리나 시간이나 썩 만족스럽진 않다. 대략 15MB에 652ms가 나온다. 그나마 메모리 제한이 128MB인 문제에 OCaml은 가비지 컬렉션 언어라 자체 어드밴티지로 +32MB를 주기 때문에 메모리는 괜찮다. 하지만 시간은 좀더 줄일 수 있을 것 같다.

#### 최적화
앞서 알파벳 빈도수를 셀 때 맵에다 그냥 쌓았다. 사실 OCaml 빌트인 맵은 [밸런스 트리](https://github.com/ocaml/ocaml/blob/4.07/stdlib/map.ml#L85) 로 구현되어 있어서 복잡도가 O(log n)이다. 문자열 길이가 최대 1,000,000 까지 가능하기 때문에 이 부분은 꽤 뼈아프다. 여길 최적화해보자.

평균 n 복잡도를 갖는 [해시 테이블](http://caml.inria.fr/pub/docs/manual-ocaml-4.07/libref/Hashtbl.html)을 쓰면 될 것 같다. 그럼 맵이 아니라 해시테이블을 만드는 함수를 다음처럼 짤 수 있다.

```ocaml
let make_hashtbl str =
  let char_seq = Seq.map Char.uppercase_ascii (String.to_seq str) in
  let hashtbl = Hashtbl.create 33 in
  Seq.iter
    (fun ch ->
      match Hashtbl.find_opt hashtbl ch with
      | None -> Hashtbl.add hashtbl ch Int32.one
      | Some cnt -> Hashtbl.replace hashtbl ch (Int32.succ cnt) )
    char_seq ;
  hashtbl
```

해시 테이블은 Persistent 타입이 아니라 Imperative 타입이라 사이드 이펙트를 통해서 다뤄야 하는 조심스러운 녀석이다. 그래서 이전 맵 버전에서는 `fold_left`를 통해 빈도수를 셌다면 여기선 `iter`를 사용했다.

이렇게 만든 해시 테이블로부터 최대 빈도수를 찾는 로직은 이전과 거의 같다. 해시 테이블을 시퀀스로 만들고 다시 시퀀스를 리스트로 만들어야 하는 번거로움은 있지만 컴파일러가 알아서 이정도는 최적화 해줄거라 믿는다.

```ocaml
let find_max_freq_hashtbl hashtbl =
  let hashtbl_list = List.of_seq (Hashtbl.to_seq hashtbl) in
  let sorted =
    List.sort (fun x y -> -Int32.compare (snd x) (snd y)) hashtbl_list
  in
  match sorted with
  | [] -> '?'
  | [one] -> fst one
  | one :: two :: _ -> if snd one = snd two then '?' else fst one
```

이번엔 리스트를 뒤집지 않고 애초에 내림차순 정렬을 해보았다.

최적화한 함수를 이용해서 메인을 다시 짜자.


```ocaml
let solve () =
  let solve_helper str =
    let freq_tbl = make_hashtbl str in
    let answer = find_max_freq_hashtbl freq_tbl in
    print_char answer
  in
  Scanf.scanf "%s" solve_helper

let () = solve ()
```

제출해보니 메모리 사용량은 비슷하지만 시간은 448ms로 대략 68% 정도로 줄었다. 오오.


이렇게 무려 OCaml로 알고리즘 문제를 나름 괜찮은 성능으로 풀어보았다. 사실 더 최적화할 여지는 남아있긴 하다. 최대 빈도수의 알파벳을 구할 때 정렬을 해서 구했는데 이러면 O(n log n) 복잡도가 들기 때문에 그냥 리스트 전체를 훑어서 O(n) 만에 구할 수도 있다. 하지만 정렬은 문자열마다 한번만 하면 되는 부분이라 크지 않아서 냅뒀다. 우선은 OCaml로도 PS를 할 수 있다는 사실에 감사하도록 하자.


##### 덧.
예전 C++14로 풀었을 때는 5MB에 40ms 였다. 제길. 힘내라 OCaml.


##### 덧 2.
내 마음속 OCaml 마스터 [끈닷넷](https://blog.kkeun.net) 님의 코멘트를 반영하여 더 최적화를 해봤다.

일단 OCaml은 여타 언어와 달리 빌트인 정수형이 32비트도 64비트도 아닌 [1비트 버린 타입](http://dev.realworldocaml.org/runtime-memory-layout.html#integers-characters-and-other-basic-types)을 쓰기 때문에 64비트 환경에서는 63비트가 된다. 이건 OCaml의 메모리 표현과 관련이 있는데 나중에 살펴보자. 암튼 `Int32`나 `Int64`는 이런 OCaml의 자연스러움을 무시하고 강제로 32비트, 64비트를 맞추기 때문에 속도 면에서 손실이다. 이거만 바꿔줬는데도 시간이 420ms로 무려 28ms나 줄었다!


다음은 빈도수를 셀 때 해시 테이블이 아닌 [배열](http://caml.inria.fr/pub/docs/manual-ocaml-4.07/libref/Array.html)을 써보자. 뭔가 배열을 쓰면 함수형이 아닌 명령형, 즉 사도의 길을 걷는 것이라고 마음속으로 여기고 있었는지 모르겠다. 거기다 개인적으로 밸런스 트리가 최애라서 ([이런 글](https://sangwoo-joh.github.io/avl-tree)을 쓰기도 하였고..), 어떤 문제든 일단 맵 부터 적용하고 보는 못된 버릇이 있다. 반성한다. 그리고 해시 테이블의 경우는 예전에 [Jane Street 블로그](https://blog.janestreet.com/what-a-jane-street-dev-interview-is-like/)에서 본 뒤로 언젠가는 써먹어야지.. 하고 생각하다보니 나타난듯 하다. 이것 역시 반성한다. 뭔가 참회의 글만 잔뜩 적어놨는데 이제부턴 코드로 말하자.


```ocaml
let make_array str =
  let char_seq = Seq.map Char.uppercase_ascii (String.to_seq str) in
  let arr = Array.make 26 0 in
  let to_idx ch = int_of_char ch - int_of_char 'A' in
  Seq.iter (fun ch -> arr.(to_idx ch) <- arr.(to_idx ch) + 1) char_seq ;
  arr

let find_max_freq_array arr =
  let to_char idx = char_of_int (idx + int_of_char 'A') in
  let third (_, _, c) = c in
  let res =
    Array.fold_left
      (fun (idx, max, answer) freq ->
        let idx' = idx + 1 in
        if max = freq then (idx', max, '?')
        else if max < freq then (idx', freq, to_char idx)
        else (idx', max, answer) )
      (0, 0, ' ') arr
  in
  third res

let solve () =
  let solve_helper str =
    let freq_arr = make_array str in
    let answer = find_max_freq_array freq_arr in
    print_char answer
  in
  Scanf.scanf "%s" solve_helper

let () = solve ()
```

모든 병목이 해결되었다!

 * 빌트인 정수 타입을 활용하여 속도 이득을 얻었다.
 * 빈도수를 셀 때 배열을 이용해서 셌다. (사실 여기서 알파벳 문자를 정수로 바꿔서 빼고... 하는 등의 행위가 내 마음속에서는 *명령형*으로 여겨져서 *함수형 접근*이라는 취지에 안맞다고 생각했나보다. 이런. 하지만 이 역시 유구한 역사와 전통이 있는 접근 방법이니 앞으론 더 넓은 마음을 갖도록 하자.)
 * 빈도수 배열을 시퀀스, 리스트 등으로 치환하지 않고 곧바로 fold 하여 계산했다. 또한 최대값을 찾기 위해서 (비록 크기 26의 작은 배열이지만) 정렬을 하지 않고 곧바로 fold와 동시에 최대값을 찾았다. 생각해보니 최대를 찾으면서 같은 값이 나오면 곧바로 결과 값을 업데이트 하면 fold로도 잘 풀린다. 이런 깔끔한 접근법을 바로 떠올리지 못하다니. 아직 머릿속에서 함수형 접근이 바로 튀어나올려면 멀었나보다.

덕분에 그 무엇보다도 빠른 276ms 의 솔루션을 얻었다. 후레이!
