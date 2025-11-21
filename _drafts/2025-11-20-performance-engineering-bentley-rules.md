---
layout: post
published: true
tag: [dev, performance]
title: 성능 엔지니어링 - 벤틀리 규칙
---

성능 엔지니어링 [2강](https://ocw.mit.edu/courses/6-172-performance-engineering-of-software-systems-fall-2018/resources/mit6_172f18_lec2/)은 벤틀리 규칙에 대한 것이다.

## 작업 (Work)
먼저 작업을 정의하자. 프로그램이 하는 (주어진 입력에 대한) "작업"이란, 프로그램이 실행한 모든 연산의 합이다.

## 최적화
그러면 작업을 최적화하는 것은 크게 두 가지로 생각해볼 수 있다.

먼저 작업 그 자체를 줄이는 일이다. 다양한 알고리즘 디자인을 통해서 작업의 양을 드라마틱하게 줄일 수 있는데, 예를 들어 단순한 $O(N^2)$의 정렬을 똑똑한 알고리즘을 통해 $O(N\text{lg}N)$ 으로 줄일 수 있다.

하지만 작업을 줄이기만 해서는 프로그램의 실제 *실행 시간*이 줄어들지 않을 수도 있다. 왜냐하면... 하드웨어가 엄청나게 복잡하기 때문이다.
 * ILP(Instruction-Level Parallelism): 어떤 명령어는 동시에 실행되기도 한다.
 * Caching, Vectorization: [1강](../performance-engineering-matrix-multiplication)에서 그 효과를 이미 경험했다.
 * Speculation, Branch Prediction

등등.

그럼에도 불구하고 작업 그 자체를 줄이는 일은 전체 실행 시간을 줄이기 위한 좋은 시작점이다.

## 벤틀리 규칙 (Bentley Rules)
원래 벤틀리 규칙은
