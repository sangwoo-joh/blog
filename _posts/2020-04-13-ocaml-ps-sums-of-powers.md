---
layout: post
tags: [ocaml]
published: true
title: OCaml로 PS 하기 -4-
subtitle: Permutation, Combination
---

최애 언어 [OCaml](https://ocaml.org/) 로 문제를 풀어보자 네 번째 시리즈다.


#### 근황
4개월 만의 포스팅이다. 그 사이에 아버지가 되면서 눈코 뜰 새 없이 너무나도 바빠져서, 문제를 꽤나 많이 풀었음에도 포스팅은 하지 못했다. 육아가 힘들다는 말만 들었지 실제로 겪어보니 정말 차원이 다르다. 이제 아들이 자는 틈을 타서 짬짬이 코딩 해야겠다. 크흑.

### [The Sums of Powers](https://www.hackerrank.com/challenges/functional-programming-the-sums-of-powers/problem)
문제풀이 사이트를 백준에서 [해커 랭크](https://www.hackerrank.com)로 바꿔보았다. 무려 "함수형 프로그래밍" 이라는 테마가 따로 있는 것이 너무 마음에 들었다.

이 문제는 입력으로 정수 $$1 \leq X \leq 1000$$와 $$2 \leq N \leq 10$$을 받아서, $$\displaystyle \sum_{x \in S} {x ^ N} = X$$ 를 만족하는 집합 $$S$$의 개수를 세는 문제이다. 조금 더 일반화하면, 가능한 모든 조합을 탐색해서 조건을 만족하는 경우를 세면 된다. 이렇게 조합을 탐색하는 알고리즘을 수도 코드로 나타내면 대충 다음과 같을 것이다.

``` ocaml
let rec pick picked =
  if P(picked) then (* base case *)
  else
    let smallest = (* possible smallest element *) in
    let maximum = (* possible maximum element *) in
    for i = smallest to maximum do
      Stack.push i picked;
      pick picked;
      Stack.pop picked
    done
```
이때까지 고른 조합 `picked` 는 가장 단순하게는 스택을 이용할 수 있다.

Base case는 이때까지 고른 `picked` 조합을 검사하여 재귀를 끝내야 하는지를 판단한다. 대부분의 문제에서는 "n 개를 조합했을 때 ..." 와 같이 명시적인 개수가 주어지지만, 이 문제에서는 앞서 말한 조건인 $$\displaystyle \sum_{x \in S} {x ^ N} = X$$ 가 된다.

이제 이걸 마음에 두고 문제를 풀어보자. 일단 $$x^N$$을 계산하는 함수는 다음과 같다.

```ocaml
let rec power x n = if n = 1 then x else x * power x (n - 1)
```

사실 이분 탐색으로 더 빠르게 동작하는 함수를 만들 수도 있지만, $$N \leq 10$$ 이라는 조건이 있으므로 이 문제에서는 이정도로 충분하다.

다음은 실제 $$X$$와 $$N$$을 받아서 개수를 세는 함수를 짜보자. OCaml에서 대문자로 시작하는 모든 변수는 모듈로 인식되므로 사용할 변수를 소문자로 썼다.

```ocaml
let solve x n =
  let max = int_of_float (sqrt (float_of_int x)) + 1 in
  let picked = Stack.create () in
  let cnt = ref 0 in
  let rec pick picked =
    let sum = Stack.fold (fun acc elt -> acc + power elt n) 0 picked in
    if sum = x then incr cnt
    else if sum < x then
      let smallest =
        if Stack.is_empty picked then 1 else succ (Stack.top picked)
      in
      for i = smallest to max do
        Stack.push i picked;
        pick picked;
        ignore (Stack.pop picked)
      done
  in
  pick picked;
  !cnt
```

일단 고를 수 있는 가장 큰 값은 $$X^{1/N}$$임을 쉽게 알 수 있다. 정확하게 이 값을 구해도 되지만 적당히 $$\sqrt{X}$$까지 구해도 괜찮을 것이다.

핵심은 실제 조합을 만들고 탐색하는 재귀함수 `pick` 이다. 우선, 지금까지 만든 조합 `picked`에 대해서 모든 $$N$$승 합 `sum`을 구한다. 그리고 이 합이 $$X$$와 같으면 개수를 증가시킨다. 그렇지않고 이 합이 여전히 $$X$$보다 작은 경우, 아직까지 더 탐색할 여지가 있으므로 그때 탐색한다. 이 부분이 작은 최적화다.

고를 수 있는 가장 값은 1이고, 이건 아직까지 만든 조합이 없을 때이다. 만약 하나라도 만든 조합이 있다면, 고를 수 있는 가장 작은 값은 만든 조합 중 가장 큰 값보다 1 큰값이다. 그 후 고를 수 있는 값의 범위 (가장 작은 값부터 가장 큰 값) 에 대해서 하나씩 조합을 만들어보고, 다시 이 조합에 대해서 탐색을 한 뒤, 바로 직전에 탐색한 값을 조합에서 빼는 방식으로 모든 탐색 공간을 훑어보면 된다.

이 문제는 모든 조합 공간을 어떻게 만들지만 고민하면 쉽게 풀리는 문제다. 까다로운 점은 Base Case 를 주어진 조건에 맞게 "이때까지 만든 조합의 $$N$$ 승의 합"을 구한 뒤 확인해야 하는 점과, 이 합이 이미 $$X$$를 넘긴 경우는 탐색하지 않아도 된다는 점이다. 이 두 가지만 잘 처리하면 쉽게 풀 수 있다.

아쉽게도 해커랭크에서는 제출한 코드의 실행 시간이나 순위가 나오진 않고, 단순히 테스트 케이스를 다 통과했는지 여부만 나온다. 그래도 무려 "함수형 프로그래밍" 섹션이 있다는 점에 의의를 두자.

#### 예고
다음은 OCamlgraph를 흉내내서 그래프 문제를 풀어볼 예정이다.
