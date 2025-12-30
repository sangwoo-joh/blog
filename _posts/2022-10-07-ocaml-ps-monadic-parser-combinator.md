---
layout: post
published: true
tags: [ocaml]
title: OCaml로 PS 하기 -7-
subtitle: 파서 컴비네이터
last_update: 2022-12-20 16:09:48
---

## 목차
{:.no_toc}

* Table of contents
{:toc}

풀고 싶었던 문제를 드디어 풀었다.

19년도 말 즈음부터 OCaml로 PS를 시작했는데, 여기에는 몇 가지 계기가 있었다. OCaml로 밥벌이를 할 수 없는 아쉬움이 가장 큰 이유였지만, "백준에서 OCaml로 PS 하기"에 결정적인 역할을 한 것은 kipa00님의 [OCaml로 문제 풀이하기](https://www.acmicpc.net/blog/view/66)라는 글이었다. 그때부터 백준에서 PS를 시작해봤고, 또 이 문제는 언젠가 꼭 풀고 싶다는 생각을 해왔다. 다만 같은 방법으로 풀면 재미없으니까 다른 방법으로 풀어봐야지 라는 생각만 어렴풋이 가지고 있었다. 하지만 정말로 이 문제를 풀기까지의 과정은 쉽지 않았다. 근본적으로는 내가 PS 자체에 익숙하지 않은 탓이 컸다. 애초에 PS를 제대로 해본 적이 없으니 당연한 일이었다. 데이터 구조와 알고리즘을 그냥 "알고" 있는 것과, 온라인 저지 사이트에서 문제를 이해하고 풀이에 필요한 것들을 코드로 모델링하고 시간 및 메모리 제한에 맞는 알고리즘을 구현해서 평가 테스트 셋을 통과하는 것은 꽤 간극이 컸다. PS는 정말로 훈련이 필요한 일이었다.

 변명을 하자면 육아와 건강 문제로 많은 시간을 쏟진 못했지만, 틈틈이 PS를 해오고 있었다. 그러다가 정말 우연히도 유튜브 추천 영상에 [Tsoding](https://www.twitch.tv/tsoding/about)이라는 트위치 프로그래머 스트리머의 [(의존성 없이) OCaml로 빠른 파서 컴비네이터 라이브러리 밑바닥부터 만들기](https://www.youtube.com/watch?v=Y5IIXUBXvLs)가 떴는데, 이건 거의 계시에 가까웠고 홀린듯 볼 수 밖에 없었다. 대략 4시간 쯤 되는 영상인데 보는 내내 힐링이었다... 이맥스로 코딩하는 모습도 구경하고... 흠흠 아무튼 이 영상 덕분에 [Monadic Parser Combinators](https://www.google.com/url?sa=t&rct=j&q=&esrc=s&source=web&cd=&cad=rja&uact=8&ved=2ahUKEwi0s7nUqrb6AhUkyYsBHUOaD-AQFnoECA0QAQ&url=https%3A%2F%2Fwww.cs.nott.ac.uk%2F~pszgmh%2Fmonparsing.pdf&usg=AOvVaw3LtR393c7YLbVqqhMb24Ty)라는 서적과 이 친구가 만든 [Parcoom](https://github.com/tsoding/parcoom)을 알게 되었고, 여기에 원래 살펴보려 했던 [Angstrom](https://github.com/inhabitedtype/angstrom/)의 코드 등 다양한 파서 컴비네이터 자료에 이틀 정도 푹 빠져서 지냈다. 그리고 드디어 이 문제를 접한지 대략 3년 정도 만에 풀게 되었다.


## [2769: 논리식 비교](https://www.acmicpc.net/problem/2769)

문제는 두 논리식이 주어졌을 때 같은지 아닌지를 판별하는 것이다. 논리식은 변수 `a-z`, 이항 연산자 `|`, `&`, `^`, 단항 연산자 `~`, 괄호 `()`, 공백으로 이루어져 있고 변수는 최대 10개, 연산자는 최대 100개이다. 연산자는 [C의 연산자 우선순위](https://en.cppreference.com/w/c/language/operator_precedence)를 따른다. 두 논리식을 구분하는 것도 구현해야 한다.

### 표현식 평가하기 (Evaluation)

일단은 파서를 뺀 나머지 부분, 주어진 표현식 두 개가 같은지 판별하는 것부터 구현해보자. 문제의 조건에 따라 변수가 최대 10개라서 가능한 진리값 조합의 수가 $$ 2 ^ {10} = 1024 $$로 작기 때문에, 이 가능한 모든 진리값의 조합을 일일이 대입해서 두 식을 평가한 다음 같은지 확인하면 된다. (문제 설명의 정규화는 반쯤은 낚시다...)

그런데 변수를 입력 그대로 `a-z` 값으로 가지고 있으면 변수에 진리값을 대입하기가 까다롭다. 변수명이 `a`부터 나타난다는 보장도 없다. 따라서 일종의 알파 변환이 필요하다. 변수가 등장한 순서대로 넘버링을 해서 정수 아이디를 변수에 매달아 두면 좋을 것 같다. 그간 PS 겉핥기를 한 덕분에 여러 조건의 조합을 표현할 때에는 비트 연산을 활용하면 좋다는 것을 어렴풋이 알고 있어서 나중에 써먹기도 좋겠다. 알파 변환은 파서가 담당해주기로 하고, 우리의 변수는 정수만을 담도록 하자.

```ocaml
type expr =
  | Var of int
  | And of expr * expr
  | Or  of expr * expr
  | Xor of expr * expr
  | Neg of expr
```

변수에 진리값을 대입해주는 함수 `f`를 받아서 표현식을 참/거짓으로 평가하는 함수 `eval`은 다음과 같다.

```ocaml
let eval ~f exp =
  let rec aux = function
    | Var id -> f id
    | Or (e1, e2) -> aux e1 || aux e2
    | And (e1, e2) -> aux e1 && aux e2
    | Xor (e1, e2) -> aux e1 <> aux e2
    | Neg e -> not (aux e)
  in
  aux exp
```

변수에 진리값을 대입해주는 함수 `f`를 어떻게 만들 수 있을지 생각해보자. 예를 들어, 식에 나타난 변수의 전체 개수가 3개라면 가능한 진리값의 조합은 총 8가지($$2 ^ 3$$)이다. 각 비트의 값이 0 또는 1이므로 이를 변수의 진리값으로 생각할 수 있다. 예를 들어 `000`은 변수 3개 모두 거짓인 조합이고, `101`는 첫 번째와 세 번째 변수는 참이고 두 번째 변수는 거짓인 조합이다. 이런식으로 생각하면 `000`부터 `111`까지 총 8개의 진리값 조합이 가능하고 이는 곧 0부터 $$ 2 ^ {3( = 변수 개수)} $$까지의 정수값과 같다.

이걸 바탕으로 변수의 진리값 조합을 나타내는 정수 `c`가 주어졌을 때 변수 `id`에 부여된 진리값을 찾는 함수 `f`를 다음과 같이 구현할 수 있다.

```ocaml
let f ~c id = c land (1 lsl id) = 0
```

이걸 가지고 진리값 조합 하나에 대해서 두 표현식이 같은지 계산하는 함수 `equal`을 구현할 수 있다.

```ocaml
let equal e1 e2 c =
  let f = f ~c in
  eval ~f e1 = eval ~f e2
```

앞서 말했듯 전체 조합은 0부터 $$ 2 ^ {변수 개수}$$만큼 가능하므로 이를 모두 살펴봐야 한다. "모두 살펴보는 작업"에는 `List.for_all`을 쓰고 싶으니 조합은 리스트로 생성하면 좋겠다. 이를 위한 `gen_comb`를 구현해보자.

```ocaml
let gen_comb n =
  let max_comb = 1 lsl n in
  let rec gen v acc = if v >= max_comb then acc else gen (v + 1) (v :: acc) in
  gen 0 []
```


표현식 두 개와 전체 변수의 개수를 입력으로 받아서, 변수 진리값의 가능한 모든 조합을 만든 뒤, 두 식이 같은지를 최종적으로 확인하는 함수는 다음과 같다.

```ocaml
let equal e1 e2 var_num =
  List.for_all (fun c -> equal e1 e2 c) (gen_comb var_num)
```

이제 남은 것은 입력 문자열을 파싱해서 두 개의 표현식과 거기 쓰인 변수의 개수를 계산하는 일이다.


## 파서 컴비네이터

파싱은 파서 컴비네이터를 이용해서 구현할 것이다. 이를 위해 파서 컴비네이터에 대해서 내가 이해한 바를 먼저 정리하고자 한다. 당연하지만 틀리거나 설명이 부족한 부분이 무조건 있을 것이므로 자세한 것은 [레퍼런스](#references)를 참조하자. 간략한 개관은 위키피디아의 [Parser combinator](https://en.wikipedia.org/wiki/Parser_combinator) 페이지에 꽤 잘 정리되어 있다.

### 컴비네이터

원래 람다 대수에서 닫힌 형태 (closed form) 의 람다식, 즉 자유 변수가 없는 람다 식을 *컴비네이터*라고 한다. 하지만 *파서 컴비네이터* 문맥에서의 컴비네이터는 [**컴비네이터 패턴**](https://wiki.haskell.org/Combinator_pattern)으로 이해하는 것이 더 좋았다.

컴비네이터 패턴이란, *패턴*이라는 이름에서 알 수 있듯이 복잡한 구조를 만들기 위해서 컴비네이터를 활용하는 디자인 패턴이다. 여기서 컴비네이터란 함수형 언어의 고차 함수 (higher-order function) 를 뜻한다. 기본적인 기능을 하는 함수 (primitives) 몇 가지를 먼저 만들고, 이 함수들을 잘 합칠 수 있는 함수 (컴비네이터) 들을 만든 다음, 이것들을 잘 조합해서 복잡한 기능을 하는 함수를 조립하는 것이다. 함수형 커뮤니티에서는 컴비네이터 패턴이 아니라 그냥 "컴비네이터"라고도 말하는 것 같다.

그리고 컴비네이터 패턴에서는 너무 당연하게도(?) 모나드가 엄청나게 쓰이는데 (...) 그래서 아예 Monadic Parser Combinator 라고 부르기도 한다. 근데 일단 나부터가 모나드에 대해서 잘 설명할 자신이 없고, 또 여기서 모나드가 무엇인지를 설명하기 시작하면 글이 안드로메다로 가버리기 때문에... 모나드에 대한 나의 이해를 짧게 정리하자면, 어떤 *귀찮고 복잡한 처리*에 **반복적으로** 쓰이는 패턴을 문법적으로 깔끔하게 처리하기 위한 디자인 패턴이다. 여기서 귀찮고 복잡한 처리에는 파이프라이닝, 사이드 이펙트, 보일러플레이트 등이 있다. 더 자세한 것은 위키피디아의 [모나드](https://en.wikipedia.org/wiki/Monad_(functional_programming)) 페이지에 더 잘 정리되어 있으니 이것을 추천한다.

여기까지 컴비네이터에 대해서 내가 이해한 바를 늘어 놓아 보았다. 따라서 *파서* 컴비네이터란, 기본적인 (프리미티브) 파서를 컴비네이터로 잘 엮어서 복잡한 구조를 파싱하는 파서를 만들기 위한 디자인 패턴이라고 이해할 수 있다.

### 파서

파서 컴비네이터의 문맥에서 파서는 문자열을 입력으로 받아서 해석한 다음 (최소) *두 가지* 값을 리턴하는 **함수**를 뜻한다. 하나는 파서가 파싱한 결과값 (e.g. 특정 글자 또는 파싱 트리) 이고, 다른 하나는 파서가 **파싱을 완료하고 남은 입력**의 정보이다. 컴비네이터는 이 남은 입력 정보를 활용한다. 프리미티브 파서들을 컴비네이터로 조합할 때, 어떤 파서의 작업이 끝난 뒤 다음 파서가 작업할 위치를 이 정보로부터 알 수 있다.

## 구현

개인적으로 글보다는 직접 구현해 보는 것이 이해에 큰 도움이 되었다. 특히 [Angstrom](https://github.com/inhabitedtype/angstrom/)과 [Parcoom](https://github.com/tsoding/parcoom) 코드가 좋았다. 여기서 구현한 코드는 순전히 이 문제를 풀기 위한 것이므로 프로덕션 레벨의 구현이 궁금하다면 [Angstrom](https://github.com/inhabitedtype/angstrom/) 코드를 보는 것을 추천한다.

### 파서의 타입

먼저 파서의 타입부터 정의해보자. 앞에서 정리한 대로 파서는 입력 문자열을 파싱한 다음 파싱 결과값과 남은 입력을 리턴하는 함수다. `Angstrom`은 여기에 부가적인 정보를 추가해둔 덕분에 (특히 엄청나게 큰 입력을 파싱하기 위한 처리가 되어 있어서) 입력 타입이 [복잡한데](https://github.com/inhabitedtype/angstrom/blob/master/lib/input.ml#L34-L40), 여기서는 입력이 작기 때문에 `string`이면 충분하다.

```ocaml
type input = string
type 'a parser = { run : input -> input * ('a, string) result }
```

입력 문자열을 파싱해서 `'a` 타입의 결과물을 만드는 파서 `'a parser`의 타입을 정의했다. 여기에는 추가로 설명할 두 가지가 있다.

먼저 파서의 타입이 곧바로 함수가 아니라 `run` 이라는 필드에 파싱 함수를 담은 레코드이다. 특별한 이유는 없고 사실 `Angstrom`과 `Parcoom`에서 모두 이렇게 했길래 관례라고 생각해서 따라했다. (...) 그냥 함수여도 전혀 문제가 없다. 다만 이렇게하면 나중에 파서 자체에 (그럴만 한게 있는지는 잘 모르겠다만) 추가적인 정보를 확장할 수도 있고, 코드를 읽을 때 "아 얘는 파서/파서 컴비네이터구나" 라는게 명시적으로 드러나는 장점이 있는 것 같았다.

두 번째는 파서가 리턴하는 "파싱 결과값"의 타입이 곧바로 `'a`가 아니라 `('a, string) result` 타입이다. `result` 는 다음과 같이 정의된 타입인데:

```ocaml
type ('a, 'b) result = Ok of 'a | Error of 'b
```

파싱 **실패**를 명시적으로 알릴 수 있는 좋은 수단이다. 곧 보게 될텐데, 어떤 파서가 *실패한 경우에* 다른 파서를 수행하는 컴비네이터가 필요하다. 그럴려면 파싱 실패를 알리는 방법이 필요하고 이를 위해 `result` 타입은 적절해 보인다. `'b` 타입에는 뭐든 괜찮은데 여기서는 디버깅 메시지를 담기 위해서 `string`을 택했다. 숏코딩을 할거라면 `unit`을 담거나 아니면 아예 결과 타입을 `option`으로 감싸도 괜찮겠다.


### 프리미티브 파서

파서 컴비네이터의 재료로 쓰일 기본적인 파서 두 개를 먼저 구현해보자.

첫 번째는 *어떤 글자든 하나*를 파싱하는 파서 `any_char`이다.

```ocaml
let any_char : char parser =
  { run =
      (fun input ->
        let n = String.length input in
        try String.sub input 1 (n - 1), Ok (String.get input 0) with
        | Invalid_argument _ -> input, Error "empty input")
  }
;;
```

입력 문자열이 비었으면 `String.sub` 호출 도중에 예외가 발생하므로 `Error`를 리턴하면 된다. `String.sub`의 마지막 파라미터가 가져올 부분 문자열의 *길이*여서 `(n - 1)`을 한 것에 주의하자.


다른 하나는 `any_char`와 거의 비슷한 일을 하지만 **입력 문자열을 소모하지 않는** 파서 `peek_char`이다. 이 파서는 [Lookahead](https://en.wikipedia.org/wiki/Parsing#Lookahead)와 같은 역할로 쓰일 수 있다.

```ocaml
let peek_char : char parser =
  { run =
    (fun input ->
      try input, Ok (String.get input 0) with
      | Invalid_argument _-> input, Error "empty input")
  }
```

이렇게 두 개의 프리미티브를 만들었다. 이것들은 이후 정의될 모나딕 컴비네이터를 통해 조립해서 우리가 원하는 불리언 표현식을 파싱하는데 쓰일 원재료가 된다.


### 모나드

파서의 타입과 프리미티브가 정의되었으니 이제 컴비네이터들을 만들자. 먼저 가장 기본적인 모나드 세 개를 정의한다. 자세한 것은 [여기](https://en.wikipedia.org/wiki/Monad_(functional_programming)#Definition)를 참조하자. 여기서부터는 타입을 같이 보는 것이 나에게는 큰 도움이 되었기 때문에 조금 장황하지만 타입을 같이 적었다.

먼저 `'a` 타입을 그대로 `'a` 모나드로 감싸주는 `return` (혹은 `unit`)이다. 달리 말하면 항상 성공해서 `v` 값을 리턴하는 *파서*를 만들어준다.

```ocaml
let return : 'a -> 'a parser =
 fun v -> { run = fun input -> input, Ok v }
```

다음으로 항상 실패하는 파서를 만들어주는 `fail`이다.

```ocaml
let fail : string -> 'a parser =
  fun err -> { run = fun input -> input, Error err }
```

마지막으로 모나드 괴담 (?) 의 주역인 바인드이다.

```ocaml
let bind : 'a parser -> ('a -> 'b parser) -> 'b parser =
  fun p f ->
  { run =
      fun input ->
        match p.run input with
        | input', Ok x -> (f x).run input'
        | input', Error err -> input', Error err
  }
;;

let ( >>= ) = bind
```

`bind p f`, 혹은 중위 연산자를 이용한 `p >>= f` 는 다음 작업을 순차적으로 수행하는 *파서*를 만든다: 먼저 파서 `p`로 입력을 파싱한다. 파싱에 성공하면 그 결과값을 함수 `f`에 적용해서 새 파서를 만든 다음 남은 입력에 대해서 수행하여 결과를 리턴한다. 파서 `p`가 파싱에 실패했다면 그대로 실패를 전파한다.

여기까지가 기본적인 모나드다. 파서 컴비네이터의 세계에는 몇 가지 모나딕 컴비네이터가 더 쓰인다.


#### 리프팅

먼저 [`lift` 패밀리 컴비네이터](https://ocaml.org/p/angstrom/0.14.0/doc/Angstrom/index.html#val-lift)를 만들 것이다. `lift` 모나드에 대한 설명은 하스켈 위키의 [lifting](https://wiki.haskell.org/Lifting)에 잘 정리되어 있다. 이 컴비네이터는 함수 하나와 여러 개의 파서를 입력으로 받아서, 입력으로 받은 파서를 *차례대로* 실행해서 값을 파싱한 다음, 파싱한 결과들을 받아서 *차례대로* 함수에 적용한 결과를 계산하는 파서를 만든다. 보통 `lift`부터 `lift2`, `lift3`처럼 함수의 입력 파라미터 개수에 따라 정의되는 것 같고 타입은 다음과 같다:

```ocaml
val lift  : ('a -> 'b) -> 'a parser -> 'b parser
val lift2 : ('a -> 'b -> 'c) -> 'a parser -> 'b parser -> 'c parser
val lift3 : ('a -> 'b -> 'c -> 'd) -> 'a parser -> 'b parser -> 'c parser -> 'd parser
```

이를 만들기 위해서는 세 가지 컴비네이터가 필요하다.


먼저 `>>|` 모나드는 다음과 같다.

```ocaml
let ( >>| ) : 'a parser -> ('a -> 'b) -> 'b parser =
  fun p f -> p >>= fun x -> return (f x)
```

`p >>| f` 는 파서 `p`를 실행해서 성공한 경우 그 결과를 함수 `f`에 적용한 값을 리턴하는 파서를 만든다. 넘겨주는 함수의 타입이 `('a -> 'b)`로, 바인드의 `('a -> 'b parser)`와는 다르다는 것에 유의하자.

그 다음 `<$>` 컴비네이터는 `>>|`의 파라미터 순서가 뒤집힌 것이다. 비유하자면 빌트인 파이프라인 연산자 `@@`과 `|>`의 관계와 같다. 이 컴비네이터는 `fmap` 이라고도 불리는듯 하다.

```ocaml
let ( <$> ) : ('a -> 'b) -> 'a parser -> 'b parser =
  fun f p -> p >>| f
```

그리고 `<*>` 컴비네이터는 다음과 같이 정의된다.

```ocaml
let ( <*> ) : ('a -> 'b) parser -> 'a parser -> 'b parser =
  fun f p -> f >>= fun f' -> p >>| f'
```

`p1 <*> p2` 는 먼저 `p1`으로 파싱한 다음 그 결과를 `p2`가 파싱한 값 (함수) 에 적용하는 파서를 만드는 컴비네이터이다.

개인적으로 모나드와 함수형 프로그래밍의 놀라운 점 중 하나는 타입만 맞추면 나머지는 잘 동작하는 점이다. 이제 위의 세 모나드를 가지고 `lift` 패밀리를 조합해보자.

```ocaml
let lift = ( <$> )
let lift2 f p1 p2 = f <$> p1 <*> p2
let lift3 f p1 p2 p3 = f <$> p1 <*> p2 <*> p3
let lift4 f p1 p2 p3 p4 = f <$> p1 <*> p2 <*> p3 <*> p4
...
```

먼저 `lift`는 `<$>`와 같다. 타입을 보면 당연하다는 것을 알 수 있다. `lift2`는 파서 두 개를 받아서 차례로 적용한 다음 파서들이 파싱한 값들을 차례대로 함수 `f`에 적용한 결과를 파싱하는 파서를 만드는 컴비네이터인데, 커링 덕분에 앞서 정의한 `<$>`와 `<*>`를 이용해서 조립할 수 있다. `lift3`과 `lift4`는 이번 문제 풀이에는 쓰이지 않지만 저런식으로 `<*>` 컴비네이터를 이용해서 `liftn`을 계속해서 만들어 갈 수 있음을 보여준다.

#### 선택 컴비네이터

두 개의 파서가 들어왔을 때 특정 파서를 선택하는 컴비네이터도 필요하다.

먼저 `Choice` 라고 불리는 컴비네이터는 다음과 같다.

```ocaml
let ( <|> ) : 'a parser -> 'a parser -> 'a parser =
  fun p1 p2 ->
  { run =
    fun input ->
      let input', result = p1.run input in
      match result with
      | Ok x -> input', Ok x
      | Error _ -> p2.run input
  }
```

즉, `p1 <|> p2` 는 `p1`과 `p2` 중 성공하는 것을 취한다. 순서는 `p1`을 먼저 시도해보고 실패하면 그 다음 `p2`를 시도한다.

이와 비슷하게 특정 결과를 버리는 컴비네이터 두 개는 다음과 같다.

```ocaml
let ( *> ) : 'a parser -> 'b parser -> 'b parser =
  fun p1 p2 -> p1 >>= fun _ -> p2

let ( <* ) : 'a parser -> 'b parser -> 'a parser =
  fun p1 p2 -> p1 >>= fun x -> p2 >>| fun _ -> x
```

`p *> q` 는 `p` 파서가 파싱한 결과는 *버리고* `q` 파서의 결과만을 취하는 파서를 만드는 컴비네이터이고, 반대로 `p <* q`는 `q` 파서가 파싱한 결과는 *버리고* `p` 파서의 결과만을 취하는 파서를 만드는 컴비네이터이다.


여기까지, 우리가 원하는 파서를 조립하기 위해서 필요한 기본 파서와 컴비네이터들을 살펴보았다. 이 문제를 풀기 위해서 반드시 필요한 컴비네이터가 두 개 남아있는데, 그 전에 먼저 지금까지 만든 것들로 파서를 어떻게 조합할 수 있는지 살펴보자.


### 파서 조합하기

지금까지 정의한 프리미티브 파서와 컴비네이터를 정리하면 다음과 같다.

 - 프리미티브: `any_char`, `peek_char`
 - 컴비네이터: `return`, `fail`, `>>=`, `>>|`, `<$>`, `<*>`, `*>`,
   `<*`, `<|>`, `lift`

아직까지 우리는 글자 하나를 무조건 받아들이는 (파싱하는) 파서와, 입력을 소모하지 않고 글자 하나를 슬쩍 살펴보는 파서 두 개만 손에 쥐고 있다. 이제 이것들을 조합해서 더 강력한 파서를 만들 것이다.

#### 기본적인 글자 파서

먼저 어떤 *조건*을 만족할 때에만 글자를 하나 파싱하는 파서를 만들어보자.

```ocaml
let satisfy f =
  peek_char >>= fun c -> if f c then any_char else fail "not satisfied"
```

만들어둔 프리미티브와 바인드 모나드가 얼마나 깔끔하게 쓰였는지 확인할 수 있다! 먼저 `peek_char`로 글자 하나를 룩어헤드로 가져와서 조건 함수 `f`에 적용한다. 조건이 참인 경우에는 `any_char` 파서를 수행하도록 해서 입력을 소모하면서 글자를 파싱하고, 그렇지 않으면 실패한다. 바인드 `>>=` 가 없었다면 아래와 같이 길어질 코드였는데 바인드 덕분에 굉장히 깔끔하게 처리된 것을 알 수 있다.

```ocaml
(* without bind *)
let satisfy : (char -> bool) -> char parser =
  fun f -> { run =
    fun input ->
      match peek_char.run input with
      | input', Ok x ->
        if (f x) then any_char else fail "not satisfied"
      | input', Error err -> input', Error err
  }
```

이제 특정 조건을 만족하는 글자 하나를 파싱할 수 있는 파서 `satisfy`를 손에 넣었으니, 이걸 이용해서 원하는 글자 하나, 알파벳 소문자 하나, 알파벳 대문자 하나, 숫자 글자 하나를 파싱하는 파서를 만들 수 있다.

```ocaml
let char x = satisfy (fun c -> c = x)
let lower = satisfy (fun c -> 'a' <= c && c <= 'z')
let upper = satisfy (fun c -> 'A' <= c && c <= 'Z')
let digit = satisfy (fun c -> '0' <= c && c <= '9')
```


글자가 아니라 *문자열*을 파싱하려면 [`take_while`](https://ocaml.org/p/angstrom/0.14.0/doc/Angstrom/index.html#val-take_while)과 같은 컴비네이터가 필요하지만, 이 문제에서는 변수가 항상 소문자 한 글자이므로 살펴보지 않을 것이다.


#### 기본적인 구조가 있는 파서

이제 바인드 말고 다른 컴비네이터를 이용해서 뭔가 구조가 있는 대상을 파싱하는 파서를 조합해보자.

먼저 괄호로 둘러쌓인 *무언가*를 파싱하는 파서 `parens`는 다음과 같다.

```ocaml
let parens p = char '(' *> p <* char ')'
```

`char '('`로 여는 괄호를 파싱한 다음 `*>` 컴비네이터를 이용해 파싱한 괄호를 **무시**하고, 그 다음 파서 `p`를 실행한다음 `<*` 컴비네이터로 닫는 괄호 `char ')'`를 **무시**한다. 파서 컴비네이터의 장점 중 하나가 바로 파싱하고자 하는 대상 언어의 문법을 거의 그대로 코드에 드러내는 것인데, 매우 취향이다.

그 다음은 같은 파서로 두 번 파싱해서 결과를 튜플로 묶어주는 파서 `pair`다.

```ocaml
let pair : 'a parser -> ('a * 'a) parser =
  fun p -> lift2 (fun e1 e2 -> e1, e2) p p
```

바로 여기에 `lift`가 쓰였다. 파서 `p`를 두 번 실행한 결과가 각각 `e1`과 `e2`에 전달돼서 `e1, e2`의 튜플을 파싱하는 파서가 만들어진다.

#### 기본적인 표현식 파서

이제 기본적인 준비는 거의 다 되었다. 앞서 정의한 표현식의 타입을 다시 살펴보자.

```ocaml
type expr =
  | Var of int
  | And of expr * expr
  | Or  of expr * expr
  | Xor of expr * expr
  | Neg of expr
```

먼저 각 배리언트를 생성하는 보조 함수들을 만들자.

```ocaml
let var_of : int -> expr = fun id -> Var id
let and_of : expr -> expr -> expr = fun x y -> And (x, y)
let or_of : expr -> expr -> expr = fun x y -> Or (x, y)
let xor_of : expr -> expr -> expr = fun x y -> Xor (x, y)
let neg_of : expr -> expr = fun x -> Neg x
```

이제 이 보조 함수들을 적절히 호출해서 표현식의 각 배리언트를 파싱하는 파서를 만들자.

#### 변수 파서

변수를 파싱하는 파서를 만들기 전에, 먼저 넘버링을 위한 데이터를 정의하자. OCaml은 명령형 프로그래밍을 잘 지원하므로 죄책감없이 레퍼런스를 사용하면 된다.

```ocaml
let id = ref (-1)

let gen_id () =
  incr id ;
  !id

let reset_id () = id := -1
```

새로운 변수가 등장할 때마다 새로운 아이디를 부여하면 된다. 변수에 아이디를 부여하는 것은 배열이나 딕셔너리 같은 맵핑 데이터 구조를 쓰면 되는데 OCaml에서는 해시 테이블이 적절해보인다. 변수를 파싱할 때에만 해시 테이블이 필요하므로 이를 파라미터로 받아오자.

```ocaml
let var : occur:(char, int) Hashtbl.t -> expr parser = fun ~occur ->
  lower >>| fun var ->
    match Hashtbl.find_opt occur var with
    | Some id -> var_of id
    | None ->
      let id = gen_id () in
      Hashtbl.add occur var id ;
      var_of id
;;
```

변수가 등장한 순서를 넘버링할 때 쓸 해시테이블 `occur`를 받아서 실제 변수를 파싱하는 파서는 위와 같다. 먼저 `lower` 파서로 소문자를 하나 파싱한다. 그리고 `>>|` 모나드를 이용해서 파싱 결과 `var`를 가져와서 표현식을 만들건데, 이때 `occur`에서 넘버링이 있으면 그걸 써서 `Var`를 만들고 없으면 새로 만든다.

#### 단항 연산식 파서

다음으로 연산자에 대한 파서를 만들어보자. 일단 가장 쉬워보이는 단항 연산식은 다음과 같다.

```ocaml
(* unary operator *)
let neg : expr parser -> expr parser = fun p -> char '~' *> (p >>| neg_of)
```

여기서는 `*>` 컴비네이터가 일종의 *조건문*으로 활용되는 것을 볼 수 있다. `~`를 만난 경우에만, 그 뒤의 표현식을 파싱한 다음 `neg_of`로 감싸준다. 이때 `~` 자체를 만났다는 사실만 중요하므로 이를 파싱한 결과 자체는 버려도 된다. `~`를 만나지 못했다면, 즉 파싱에 실패했다면 아무것도 하지 말아야 하므로 컴비네이터의 의도와도 잘 맞다.

그런데 이 파서의 타입을 잘 보면 `expr parser`가 아니라, 부정 연산으로 만들기 위한 대상 표현식을 파싱하기 위해서 타입이 `(expr parser -> expr parser)`인 것을 알 수 있다. 표현식 파서를 만들려고 단항 연산식 파서를 만들려는데, 입력으로 표현식 파서가 들어와야 한다니 조금 모순된 상황이다. 이에 대해서는 곧 설명할 Fixed Point 컴비네이터가 해결해준다.

#### 이항 연산식 파서

```ocaml
(* binary operators *)
let and_ : (expr -> expr -> expr) parser = char '&' *> return and_of
let or_ : (expr -> expr -> expr) parser = char '|' *> return or_of
let xor : (expr -> expr -> expr) parser = char '^' *> return xor_of
```

이항 중위 연산의 경우는 조금 더 복잡하다. 중위 연산 표현식을 제대로 파싱하려면 (1) 왼쪽항의 *표현식*을 먼저 파싱한 다음, (2) 중위 연산자를 파싱하여 그에 맞는 배리언트의 생성자를 꺼내오고, (3) 오른쪽항의 *표현식*을 마저 파싱해서 (4) 최종적으로는 좌항과 우항의 식을 생성자로 묶어야 한다. 위의 함수들은 (2)의 역할을 하는 함수들이다. 이 과정을 다른 언어로 구현했다면 스택을 이용해서 구현했겠지만, 파서 컴비네이터로는 좀더 깔끔하게 할 수 있다.

위의 (1)-(4) 과정을 조금 더 일반화해서, 중첩된 중위 표현식을 파싱하는 과정은 다음과 같다.
 1. 먼저 가장 왼쪽항을 파싱한다.
 2. 왼쪽항 다음의 중위 연산자와 표현식 하나를 파싱한다.

    2.1. (a) 파싱에 성공한 경우, 중위 연산자의 생성자로 이때까지
       파싱한 결과를 묶는다. 그리고 (b) 다시 2.로 돌아가서 중위
       연산자와 표현식 하나를 계속해서 파싱한다.

    2.2. 파싱에 실패한 경우, 이때까지 파싱한 결과를 곧바로
       리턴한다. 만약 중위 연산자 파싱에 처음부터 실패했다면 곧바로
       1.의 왼쪽항을 리턴한 것과 같다.

이 과정은 파싱하고자 하는 대상이 조금만 복잡해져도 필수적이다. 딱히 정해진 이름이 있는 것 같진 않지만 [Angstrom에서는 `chainl1`](https://github.com/inhabitedtype/angstrom/#usage)이라는 함수가 있더라. 아마 '왼쪽항 1개'를 누적해가면서 파싱해간다는 뜻이 아닐까 싶다. 나도 유사하게 `chain`이라는 함수를 정의했다.


```ocaml
let chain expr op =
  let rec further acc =
    (* 2. *)
    lift2 (fun constructor x -> constructor acc x (* 2.1. (a) *) ) op expr
    >>= further (* 2.1. (b) *) <|> return acc (* 2.2. *)
  in
  expr (* 1. *) >>= fun init -> further init
;;
```

함수는 위의 과정을 거의 그대로 따라가고 있다. 1:1 대응은 아니지만 위의 과정에 해당하는 부분을 주석으로 적어두었다. 먼저 `expr`로 표현식을 파싱하는데, 이는 가장 왼쪽항이므로 중위 연산 체이닝의 초기값이다. 그래서 `>>=` 에 넘겨줄 때 `init`으로 네이밍했다. 그 후 중위연산자를 만날 때마다 계속해서 그에 맞는 생성자 (`constructor`) 를 호출해서 중위 표현식을 누적한다. 이 리프팅의 결과를 가지고 다시 `further`를 호출해서 앞에서 말한 과정을 반복하거나, 혹은 반복에 실패 (정확히는 리프팅의 첫 번째 파서인 `op`, 즉 연산자 파싱에 실패) 한 경우 이때까지 쌓은 결과값을 곧바로 리턴한다. 내 취향의 코드다.

`lift2`에 전달한 함수 파라미터와 파서의 순서에 주목하자. `init`에서 이미 왼쪽항의 표현식을 파싱했으므로 그 다음은 중위 연산자 `op`를 파싱하고 그 다음 표현식 `expr`을 파싱해야 한다. 그리고 리프팅 함수에 있는 생성자 (`constroctur`) 가 바로 위에서 정의한 이항 연산자 파서들 `and_`, `or_`, `xor`이 파싱한 결과 `and_of`, `or_of`, `xor_of`인데, 이전에 파싱해서 누적된 `acc`가 먼저 온 것을 볼 수 있다. 예를 들어 `a + b + c`를 체이닝하게 되면 `((a + b) + c)`로 묶여야 하는 것과 같다. 함수형에서의 `fold_left` 와도 비슷하다.

이제 우리는 이항 연산자 (의 생성자를 돌려주는) 파서 `and_`, `or_`, `xor`과, 중위 연산식을 체이닝할 수 있는 컴비네이터 `chain`을 이용해서 중위 연산식 파싱할 수 있을 것 같다. 그런데, 단항 연산 파서의 타입과 마찬가지로, 이항 연산의 좌항과 우항을 파싱하려면 표현식 파서가 있어야 한다. 그런데 지금 우리가 만들려고 하는게 표현식 파서다. 뭔가 모순적인 상황임을 알 수 있다. 표현식 파서를 만들려고 하는데 표현식 파서가 필요한 것이다. 그 이유는 표현식 자체가 **귀납적으로** 정의된 타입이기 때문이다. 따라서, *귀납적인 자료구조를 파싱할 수 있게 해주는 컴비네이터*가 필요하다.

#### Fixed Point 컴비네이터

X를 파싱하기 위해서 X 파서가 필요한 상황은 사실 프로그래밍 언어의 세계에서는 흔한 일이다. 예로 JSON을 생각해보자. JSON의 배열 혹은 오브젝트에 들어갈 수 있는 값은 그 자체로 JSON이다. 이런 재귀적인 값을 파싱하는 파서 컴비네이터는 어떻게 만들어야 할까?

OCaml에는 재귀적인 값을 정의할 수 있게 해주는 키워드 `rec`이 있으니, 다음과 같이 구현하면 어떨까?

```ocaml
let rec expr : expr parser =
  neg expr <|> parens expr <|> var ~occur
```

하지만 이렇게하면 다음과 같은 에러 메시지가 뜬다:

```
This kind of expression is not allowed as right-hand side of `let rec'
```

대체 무슨 일이 일어난건지 [매뉴얼](https://v2.ocaml.org/manual/letrecvalues.html#s:letrecvalues)을 좀 찾아보니, 몰랐던 사실 하나를 깨달았다. OCaml에서 `let rec` 키워드로 만들 수 있는 재귀적인 값에는 제한이 있었다: **함수가 아닌 값**만 가능하다. 이게 무슨 말이냐 하면...
 - `let rec expr foo bar = ... `에서 `expr`은 **함수** 다.
 - `let rec expr = ...` 에서 `expr`은 **값** 이다.

즉, 파라미터 없이 `let` (또는 `let rec`) 로 선언된 이름은 항상 값이다. 그러므로 값을 정의하는 본문 안에서 이를 함수로 쓸 수 없다! (우리의 파서 타입은 `run`을 담은 레코드이지만, 실제로 `run`의 타입이 함수이기 때문에 타입 체커가 이렇게 동작한다)

그러면 의미없는 파라미터를 줘서 강제로 함수로 만들면 되지 않을까?

```ocaml
let rec expr () =
  neg (expr ()) <|> parens (expr ()) <|> var ~occur
```

이렇게하면 타입 검사는 통과하지만, 코드를 제출하면 **메모리 초과**가 뜬다. `neg` (또는 `parens`) 컴비네이터에 넘겨줘야 하는 타입은 파서인데, 이를 만들기 위해서 `expr ()` 이라는 함수를 호출하고, 그러면 호출한 `expr ()` 안에서 또 컴비네이터에 넘겨줄 파서를 만들기 위해서 호출하고... 의 과정을 거쳐 스택 오버플로우가 발생하는 것이다.

그러면 대체 어떻게 해야 재귀적인 파서를 만들어주는 컴비네이터를 만들 수 있을까?

막혔을 때는 망설임없이 선인들의 지혜를 살펴보는 것이 좋다.

먼저 이론적인 배경을 람다 대수에서 찾아볼 수 있다. [Fixed-point combinator](https://en.wikipedia.org/wiki/Fixed-point_combinator)를 이용하면, 어떤 fixed point가 존재하는 함수 f에 대해서, 이 컴비네이터 fix를 이용하면 fix f 를 계산할 수 있고 보통 fix f = f (fix f) 와 같이 계산된다. 특히 하스켈 커리가 구현한 Y combinator는 다음과 같다.

$$ Y = \lambda f. (\lambda x. f (x x)) (\lambda x. f (x x)) $$

OCaml에서는 간단하게 다음과 같이 단순한 Y combinator를 구현할 수도 있다.

```ocaml
let rec fix f x = f (fix f) x

(** example *)
let fact f = function
  | 0 -> 1
  | x -> x * f (x - 1)

let factorial = fix fact

let _ = factorial 5 (* evaluates to 120 **)
```

우리가 관심있는 파서로 돌아와보자. `Angstrom`에는 [`fix`](https://ocaml.org/p/angstrom/0.14.0/doc/Angstrom/index.html#val-fix)라는 함수가 있는데, 이 함수가 바로 이름 그대로 어떤 파서의 Fixed-point 를 계산해내는 역할을 한다. 다음과 같이 짧은 구현으로 이루어져 있다.

```ocaml
let fix : ('a parser -> 'a parser) -> 'a parser =
  fun f ->
    let rec p = lazy (f r)
    and r = { run = fun input -> (Lazy.force p).run input } in
    r
```

즉, 람다 대수의 Y combinator와 유사하게, 재귀적인 함수를 정의하기 위해 정의하려고 하는 대상 함수(여기서는 파서 f)를 파라미터로 받아서, 이를 이용해서 새로운 재귀적인 함수(파서)를 계산하는 함수이다. `Angstrom`은 [Lazy evaluation](https://en.wikipedia.org/wiki/Lazy_evaluation)을 이용해서 이를 구현하고 있는데, `Lazy`를 벗겨내면 위 코드는 아래 코드와 동일하다.

```ocaml
let fix f =
  let rec r = { run = fun input -> (f r).run input } in
  r
```

람다 대수와 완전히 동일하진 않지만, Y combinator와 유사하게 정의하고자 하는 재귀적인 파서를 파라미터로 받아서 (즉, $$\lambda f.$$) 이 함수를 사용하는 새로운 파서를 계산해내는 (즉, $$(\lambda x. f ...)$$) 모습을 따르고 있다.

예를 들어, 우리의 표현식을 생각해보자. `Var`를 제외한 나머지 타입은 귀납적으로 정의되어 있어서, `expr`을 파싱하려면 `expr` 파서를 호출해야 한다. 따라서 코드를 다음과 같이 작성할 수 있다:

```ocaml
let expr = fix (fun expr -> var <|> parens expr <|> ... )
```

여기서 `fix`에 전달된 함수 파라미터 `expr`은 정의하고자 하는 표현식 파서 `expr`과 같다.


### 표현식 파서 (드디어)

이제 우리 손에 있는 고급 파서들과 다양한 컴비네이터들을 이용하면 드디어 표현식 파서를 만들 수 있을 것 같다. 나이브하게는 다음과 같이 구현할 수 있다.

```ocaml
let expr ~occur =
  fix (fun expr ->
    let factor = fix (fun factor ->
        neg factor <|> parens expr <|> var ~occur))
     in
    chain factor and_ <|> chain factor xor <|> chain factor or_
```

체이닝과 Fixed point 컴비네이터를 이용해서 `factor`와 중위 연산식을 파싱했다. `factor`는 단항 연산식이거나, 괄호로 둘러쌓인 표현식 그 자체이거나, 변수이다. 표현식은 `factor`가 `and`, `xor`, `or` 중위 연산으로 계속 체이닝될 수 있다.

하지만 이렇게 파싱해서 제출하면 틀린 답이 나온다. 왜냐하면 위의 파서는 **연산자의 우선순위**를 고려하지 않았기 때문이다. 문제의 조건인 C의 연산자 우선순위에 따르면 `~`, `&`, `^`, `|` 순이다. 마지막 `<|>` 컴비네이터에 묶인 순서가 `and_`, `xor`, `or_`이니 우선순위를 지킨게 아닌가 하는 생각이 들 수도 있지만, 실제로는 그렇지 않다. 예를 들어 `a | b & c` 를 파싱하면 `(a | (b & c))`로 파싱되어야 하는데, 위의 파서는 `((a | b) & c)`로 파싱하게 된다. 즉, `<|>` 컴비네이터는 우선순위를 부여하지 못한다.

어떻게 우선순위를 줄 수 있을까? 파서 컴비네이터에서 우선순위를 주는 방법은 매우 간단하다: 대상 언어의 **문법**을 정확히 작성하는 것이다. BNF에서는 논터미널의 심볼의 깊이가 깊을수록 우선순위가 높다. 따라서 단항 연산자 `~`가 가장 깊숙한 곳에 있고, 그 후 순서대로 `&`, `^`, `|`가 있는 문법을 정의하면 된다.

```
EXPR := TERM0 or TERM0
      | TERM0

TERM0 := TERM1 xor TERM1
      | TERM1

TERM1 := FACTOR and FACTOR
      | FACTOR

FACTOR := VAR
       | ( EXPR )
       | not FACTOR
```

이 올바른 문법을 바탕으로 정확한 표현식 파서를 만들 수 있다.

```ocaml
let expr : occur:(char, int) Hashtbl.t -> expr parser = fun ~occur ->
  fix (fun (expr : expr parser) ->
      let factor =
        fix (fun factor -> neg factor <|> parens expr <|> var ~occur)
      in
      let term1 = chain factor and_ in
      let term0 = chain term1 xor in
      chain term0 or_ )
```

드디어 표현식 파서를 완성했다! 문법을 거의 그대로 닮은 아름다운 코드이다.

이제 남은 일은 입력을 다듬어서 파싱한 뒤 두 식을 비교하고 문제의 조건에 맞게 출력하는 것이다. 입력 표현식은 공백도 포함하는데, 우리는 공백을 파싱하는 파서는 따로 만들지 않았다. 괄호와는 달리 공백은 표현식의 의미에 영향을 끼치지 않아서 그냥 전처리로 공백을 없애버리는 것이 훨씬 쉽기 때문이다. 공백을 없애는 `remove_blanks`를 만들어서 입력을 다듬자.

```ocaml
let remove_blanks s =
  String.to_seq s |> Seq.filter (fun c -> c <> ' ') |> String.of_seq
```

파이프라이닝 코드는 역시 내 취향이다.

이제 최종적으로 문자열을 입력으로 받아서 우리가 만든 표현식 파서로 파싱을 하는 함수를 구현할 수 있다. 파서 컴비네이터를 올바르게 구현했다면 두 표현식을 구분하는 일은 아주 쉽다: 그냥 순차적으로 두 번 파싱하면 된다. 같은 파서를 두 번 적용해서 튜플로 만들어주는 컴비네이터 `pair`를 이용하면 좋을 것 같다.

```ocaml
let parse_expr s =
  let occur = Hashtbl.create 10 in
  reset_id () ;
  let input = remove_blanks s in
  let expr_parser = pair (expr ~occur) in
  match expr_parser.run input with
  | _, Ok r -> (r, Hashtbl.length occur)
  | _, Error e -> failwith e
;;
```

이렇게 파싱한 두 개의 표현식과 변수 개수를 가지고 앞에서 정의한 `equal` 함수를 이용해 모든 조합을 비교하고 결과를 출력 형태에 맞게 잘 출력하면 4ms의 솔루션을 얻을 수 있다. 자세한 코드는 [여기](https://github.com/sangwoo-joh/ocaml-ps/blob/master/boj/2769.ml)서 확인할 수 있다.


---

정말 오랜만에 OCaml PS 시리즈 글을 썼다. 문제 푸는데는 이틀 정도 걸렸는데 이 글을 쓰는데는 2주가 넘게 걸린 것 같다. 만족스럽게 쓰여진 부분도 있지만 몇 번을 읽어도 부족해보이는 부분도 많다. 역시 글쓰기는 어렵다.

올해는 OCaml 5.0이 세상에 공개된 뜻깊은 해이다. 드디어 Parallelism과 Concurrency가 언어 레벨에서 지원된다. OCaml로 직업적인 코딩을 할 수는 없으니 아마도 당분간 5.0을 쓸 기회는 없겠지만, 사람 일이라는 게 어떻게 될지 모르니 일단은 내가 할 수 있는 방법인 "OCaml로 PS 하기"라도 꾸준히 할 수 있길 바란다.

---

## References
 - [OCaml로 문제 풀이하기](https://www.acmicpc.net/blog/view/66)
 - [Angstrom](https://ocaml.org/p/angstrom/0.14.0/doc/Angstrom/index.html)
 - [Fast Parser Combinator Library from Scrach in OCaml (no dependencies)](https://www.youtube.com/watch?v=Y5IIXUBXvLs)
 - [Parcoom](https://github.com/tsoding/parcoom)
 - [Monadic Parser Combinators](https://www.google.com/url?sa=t&rct=j&q=&esrc=s&source=web&cd=&cad=rja&uact=8&ved=2ahUKEwi0s7nUqrb6AhUkyYsBHUOaD-AQFnoECA0QAQ&url=https%3A%2F%2Fwww.cs.nott.ac.uk%2F~pszgmh%2Fmonparsing.pdf&usg=AOvVaw3LtR393c7YLbVqqhMb24Ty)
 - [Combinator pattern](https://wiki.haskell.org/Combinator_pattern)
 - [Parser combinator](https://en.wikipedia.org/wiki/Parser_combinator)
 - [Monad](https://en.wikipedia.org/wiki/Monad_(functional_programming))
 - [Recursive descent parser](https://en.wikipedia.org/wiki/Recursive_descent_parser)
 - [Tying-the-knot](https://wiki.haskell.org/Tying_the_Knot)
 - [Lazy evaluation](https://en.wikipedia.org/wiki/Lazy_evaluation)
