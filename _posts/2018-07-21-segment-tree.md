---
layout: post
tags: [cs]
title: 세그먼트 트리
subtitle: 자료 구조란 어려워
published: true
---
 알고리즘 준비를 하다가 만난 문제다. 주어진 배열에서,

  1. 어떤 구간의 합을 구하는 쿼리
  2. i번째 원소를 업데이트하는 쿼리

 이 두 종류의 쿼리를 주어진 횟수만큼 시행해야 하는 상황이 있다고
 하자. 나이브하게 접근하면 1번 구간 합은 O(N), 2번 업데이트에 O(1)이
 걸리므로 K번 시행한다고 하면 O(KN)의 복잡도를 갖는다.

 업데이트 쿼리가 없다면 그저 부분합을 저장해뒀다가 돌려주는 방식으로
 O(1)만에 가능하다. 그러나 원소가 업데이트 되어야 한다면, 해당 원소가
 포함되는 모든 부분합을 다 업데이트 해줘야 하므로 결국 O(N)이 걸린다.

 이럴 때 정답은 [**세그먼트 트리**] 이다.

 세그먼트 트리는 트리의 성질을 활용해서 위의 두 쿼리를 모두
 O(logN)만에 해치워 버릴 수 있게 도와주는 자료구조이다.

 기본은 Complete Binary Tree의 array index 계산 방법을
 가져온다. Complete Binary Tree를 array로 구현하면, 어떤 node index
 i의 부모는 `i/2`, 왼쪽 자식은 `2*i`, 오른쪽 자식은 `2*i+1`이 된다(단,
 index가 1부터 시작하는 경우에만 해당).

 이걸 이용해서 루트는 전체를 담고, 루트의 자식들은 전체의 반반씩을
 담고, 또 반반씩을 담고... 하는 식으로 쭈욱 가다보면 리프에는 그냥
 array element 하나를 담게 된다. 그러면 대충 init 함수 모양은 이렇게
 될 것이다:

```c++
int init(int id, int l, int u){
  if (l == u) tree[id] = array[l];
  else tree[id] = init(2*id, l, (l+u)/2)
                + init(2*id+1, (l+u)/2+1, u);

  return tree[id];
}
```

 공간을 좀 낭비하긴 하지만 (대략 원래 array 크기의 4배로 잡으면 ㅇㅋ),
 이렇게 구조를 잡아두면 합/업데이트를 다음과 같이 계산할 수 있다:

```c++
int sum(int id, int l, int u, int query_l, int query_u){
  if (query_l > u || query_u < l) return 0;
  if (query_l <= l && u <= query_r) return tree[id];

  return sum(2*id, l, (l+u)/2, query_l, query_u)
       + sum(2*id+1, (l+u)/2+1, u, query_l, query_u);
}

void update(int id, int l, int u, int u_idx, int u_delta){
  if (u_idx < l || u_idx > u) return;

  tree[id] += u_delta;
  if (l != u){
    update(2*id, l, (l+u)/2, u_idx, u_delta);
	update(2*id+1, (l+u)/2+1, u, u_idx, u_delta);
  }
}
```

 `update`에서 업데이트 하는 배열 원소의 값 자체가 아니라 값의 변화
 값(`u_delta`)을 넘기는 것에 유의해야 한다. 그렇게 해야 바뀌는 원소가
 영향을 주는 모든 구간(노드)에 값을 전파하기 편하기 때문이다. 그리고
 이 업데이트 함수는 **세그먼트 트리**를 업데이트 하는 함수임을
 주의해야 한다. **실제 배열 원소는 따로 업데이트 해줘야한다!!**
 그러니까, 예를 들어 `update(1, 0, N-1, 3, new - array[3])`이 호출되면
 (즉 크기 N 짜리 배열의 4번째 원소(= index가 3)의 값이 new로 바뀌면),
 update 함수 호출 뒤에 `array[3] = new;`라고 따로 배열만 업데이트
 해주면 된다. 잊지말자. 우리는 지금 **세그먼트 트리**를 다루고 있을
 뿐, 원래의 배열은 건들지 않았다. 이걸 까먹어서 오답이 나는 경우가
 있었다.

 마지막으로 주의할 점은 노드의 아이디를 계산할 때 `left = 2 * id`,
 `right = 2 * id + 1`로 계산했기 때문에, `init`, `update`, `sum`을
 호출할 때 루트 노드의 아이디를 1로 넘겨줘야 한다는 점이다. 예를 들어
 `array[N]` 즉 크기 N 짜리 배열로 값을 다룬다면, 세그먼트 트리를
 초기화 할 때는 `init(1, 0, N-1);`를 호출해주면 된다.

 이제 우리는 큰 배열의 원소들이 연속적인 성질을 가질 때, 자주 원소가
 업데이트 되기도 하고 배열의 연속된 구간에 어떤 쿼리가 들어오기도 하는
 그런 상황에 적합한 자료 구조 하나를 알게 되었다. 이 포스트에는 구간의
 합을 예시로 들었지만 구간의 최대값/최소값을 저장한다던가 하는
 세그먼트 트리도 얼마든지 가능할 것이다.
