---
layout: post
tags: [ocaml]
published: true
title: OCaml로 PS 하기 -2-
subtitle: 힘을 내.. OCaml
---

최애 언어 [OCaml](https://ocaml.org/) 로 문제를 풀어보자 두 번째 시리즈다.

### [1152번: 단어의 개수](https://www.acmicpc.net/problem/1152)
사실 이거 금방 풀었던 거라 자기 전에 가볍게 풀고 자려고 잡았다가 된통 당했다.

문제 자체는 아주 심플하다. 길이 1,000,000 미만의 문자열 하나가 들어올 건데, 대/소문자와 띄어쓰기만 담겨있고 문자열 앞뒤에는 공백이 있을 수 있으며 연속된 공백은 없다. 이 경우 공백으로 구분되는 단어의 수를 세는 문제다.

문자열 앞/뒤에 공백이 있는 경우를 제외하면 그냥 전체 `문자열의 공백 수 + 1` 하면 되는 문제다. 앞뒤 공백만 처리해주면 된다.

하지만 OCaml은 함수형 접근이 가능한 친구! 나는 곧바로 다음과 같은 함수를 짜기 시작했다. `Scanf.scanf`는 공백을 구분자로 인식하기 때문에 공백이 포함된 긴 문자열을 입력으로 받을 수 없어서 이번에는 `read_line ()`을 썼다.

```ocaml
let count_words str =
  let splited = String.split_on_char ' ' str in
  let filtered = List.filter (fun x -> String.length x > 0) splited in
  List.length filtered

let solve () =
  let input = read_line () in
  print_int (count_words input)

let () = solve ()
```

가독성을 위해서 중간 변수를 썼을 뿐이지 사실 한 줄로도 가능한 코드이다. `String.split_on_char` 를 이용해서 공백을 기준으로 다 쪼개버리고, 길이 0 인 (즉 공백인) 친구들을 필터링 하고 남는 단어 리스트의 길이를 돌려주는, 아주 명확한 함수다. 예전에 애먹였던 테스트 케이스들 (e.g. " a " 라던가, " a" 라던가, "a " 라던가, "" 라던가...) 도 로컬에서 잘 통과했기에 문제없이 풀었다고 생각하고 제출했다.

그러자 **런타임 오류**가 떠버렸다.

![what?](/assets/img/kejang_what.jpg)

아니 *메모리 초과*나 *시간 초과*가 아니라 런타임 오류..? 오답도 아니고 런타임 오류라고? 타입-안전한 우리 OCaml 친구가? 내가 놓친 코너 케이스가 있는 것인가? 싶어서 1 시간 이상을 요리조리 디버깅 해보고, 채점에 사용된 버전인 4.07.0 버전 소스도 받아다 뜯어보았으나 `String.split_on_char` 에서 unsafe C FFI를 사용하는 부분이 수상하다는 것외에는 딱히 소득이 없었다. 사실 야근하고 와서 졸린 머리로는 깊이 파보고 싶지 않았다.

그래서 결국 함수형 접근은 포기하고 다음처럼 짜서 통과하긴 했다 (...)

```ocaml
let to_array str =
  let arr = Array.make (String.length str) ' ' in
  String.iteri (fun idx ch -> arr.(idx) <- ch) str ;
  arr

let solve () =
  let input = read_line () in
  let arr = to_array input in
  let count =
    Array.fold_left (fun acc at -> if at = ' ' then acc + 1 else acc) 0 arr
  in
  let first, last = (arr.(0), arr.(Array.length arr - 1)) in
  let count =
    match (first, last) with
    | ' ', ' ' ->
        count - 2
    | ' ', _ | _, ' ' ->
        count - 1
    | _, _ ->
        count
  in
  print_int (count + 1)

let () = solve ()
```

이것도 처음엔 `String.to_seq` 가지고 짰는데, `Seq`가 in-place 변환이 아니었다. (졸려서 깊이 파보진 않았으나) 뭔가 임의의 순서로 문자 리스트를 정렬하는 바람에, ` a ` 를 입력으로 줫더니 `[| ' ', ' ', 'a' |]` 가 나와버렸고 이거 때문에 또 20 여분을 날린 것 같다 (...) 어쨌든 (내 마음 속) 함수형 접근을 포기하고 대략 68ms 정도의 괜찮은 답안이 통과되었다. Phew.


5분이면 풀고 잘 문제라고 생각없이 시작했다가 늦게 잠들게 되어 버렸다. 역시 최애 언어이지만 마이너 언어로 PS를 도전하는 일은 만만치 않다. 쉽게 풀었던 문제도 만만하게 보고 덤비지 말자.


##### 덧.
끈닷넷님의 덧글이 훨씬 빨라보인다. 한번 구현해보자. `String.trim` 이란 함수가 있는지 몰랐다. 표준 라이브러리 문서를 좀더 꼼꼼하게 읽어봐야겠다. 파이썬에도 `strip()` 이란 친구를 참 애용했는데 역시 내 최애 언어다.

```ocaml
let count_words str =
  let str = String.trim str in
  let spaces = ref 0 in
  let count_space ch = if ch = ' ' then incr spaces in
  String.iter count_space str ;
  !spaces + 1

let solve () =
  let input = read_line () in
  print_int (count_words input)

let () = solve ()
```

깔끔하다. `String.trim` 으로 앞뒤 공백을 잘 제거했고 남은건 그냥 공백만 세면 된다.

그런데 이대로 제출하니 **오답**이다. 아니? 맞왜틀? 다시 찬찬히 살펴보니 빈 문자가 들어오는 경우를 처리해주지 않았구나. `count_words`에 한 줄만 추가하면 된다.

```ocaml
let count_words str =
  let str = String.trim str in
  let spaces = ref 0 in
  let count_space ch = if ch = ' ' then incr spaces in
  String.iter count_space str ;
  if String.length str = 0 then 0 else !spaces + 1
```

이것으로 최종 24ms의 답안에 성공했다. 예이!
