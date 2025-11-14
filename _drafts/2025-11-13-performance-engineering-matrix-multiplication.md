---
layout: post
published: true
tag: [dev, performance]
title: 성능 엔지니어링 - 행렬 곱셈 이야기
---

발단: 평소처럼 재미있는 글이 없나 하고 [긱뉴스](https://news.hada.io/)를 탐방하다가 [컴파일러 엔지니어가 되는 법](https://rona.substack.com/p/becoming-a-compiler-engineer)이라는 글을 보게 되었다. 한국에서만 컴파일러 관련 포지션이 적은건가 싶었는데 미국도 상황은 비슷한가보구나, 라고 생각하면서 읽다가, 저자의 추천 MIT OCW [Performance Engineering](https://ocw.mit.edu/courses/6-172-performance-engineering-of-software-systems-fall-2018/) 강의를 만나게 되었다. 마침 최근 내 관심사와 맞닿아 있는 주제라서 강의 슬라이드를 보고 있는데 너무 재밌어서 내 식으로 소화도 할 겸 좀 정리해보려고 한다. 마침 [MIT OpenCourseWare 라이센스](https://ocw.mit.edu/pages/privacy-and-terms-of-use/)도 출처만 표기한다면 너그러운 편이다.

[1강](https://ocw.mit.edu/courses/6-172-performance-engineering-of-software-systems-fall-2018/resources/lecture-1-introduction-and-matrix-multiplication/)은 성능 엔지니어링 전반에 대한 이야기를 시작으로, 행렬 곱셈을 어디까지 최적화할 수 있는지에 대한 이야기이다.

## 성능
소프트웨어를 만들 때는 성능보다 더 중요하게 고려해야 하는 속성들이 있다. 호환이 잘 되는지, 올바르게 동작하는지, 원하는 기능이 잘 동작하는지, 신뢰도는 어떤지, 코드는 분명한지, 유지보수는 얼마나 용이한지, 다른 모듈과의 조립은 얼마나 용이한지, 이식성은 좋은지, 테스트하기 좋은지, 사용성이 좋은지, 디버깅하기 좋은지, 강건한지(Robustness) 등등.

성능은 이러한 속성을 "살 수 있는" 일종의 화폐라고 볼 수 있다. 즉, 우리는 성능을 희생해서 유지보수성을 높일 수 있고, 성능을 희생해서 디버깅하기 좋은 코드를 만들 수 있고, 성능을 희생해서 모듈성을 높일 수 있다. 그러니까 소프트웨어 엔지니어링의 모든 분야가 늘 그렇듯 균형(Trade-Off)을 고려해야만 한다.

아주 초창기 컴퓨팅 하드웨어의 파워가 빈약했던 시절에는 하드웨어의 비용 문제도 있었지만, 일정 수준의 성능이 받쳐주지 않으면 애초에 프로그램 자체를 돌릴 수 없는 경우도 많았다. 그래서 이 시절에는 앞서 말한 소프트웨어의 다양한 중요한 속성들을 많이 희생하면서 성능에 집중하기도 했다. 그러다보니 섣부른 최적화와 관련해서 많은 교훈들이 알려져 있다.

> Premature optimization is the root of all evil. - Donald Knuth

아마도 도널드 크누스의 이 문장이 가장 유명할 것이다. 섣불리 최적화하면 큰일난다.

> More computing sins are committed in the name of efficiency (without necessarily achieving it) than for any other single reason - including blind stupidity. - William Wulf

이 말은 72년에 ACM 컨퍼런스에서 발표된 논문 "A Case Against the GOTO" 에서 나온 말이다. 교과서에서 배웠던 "GOTO 쓰지마세요"를 주장한 논문이라고 한다. 실제로 성능 개선을 이루지 못하면서도 효율성이라는 이름 하에 저질러지는 나쁜 프로그래밍 관행이 아주 많으니, 효율성을 과도하게 쫓지 말라는 경고를 담고 있다.

> (Jackson's Rules of Optimization) The first rule of program optimization: Don't do it. The second rule of program optimization - for experts only: don't do it yet. - Michael Jackson

마이클 잭슨은 낚시가 아니라 영국의 컴퓨터 과학자 [마이클 A. 잭슨](https://en.wikipedia.org/wiki/Michael_A._Jackson_(computer_scientist)#:~:text=Michael%20Anthony,the%20UK.)이다. 잭슨의 최적화 규칙으로 알려진 이 말은 초기의 과도한 최적화가 코드의 복잡성을 높이고 버그를 유발하니까 되도록 피하고 나중에 필요한 부분만 최적화하라는 교훈을 담고 있다.

그런데 무어의 법칙에 따라 시간이 지나면서 하드웨어, 특히 단일 칩의 성능이 비약적으로 발전하기 시작했다. 비유하자면 성능이라는 화폐를 마구 찍어내는 시기였다. 하지만 그것도 2004년까지였고, 그 이후에는 물리적인 한계로 인해 프로세서의 클럭 스피드가 예전만큼 극적으로 증가하지는 않게 되었다.

그래서 하드웨어 제조사들은 단일 칩의 성능을 개선하는 것에서 벗어나서 여러 개의 코어를 탑재하는 쪽으로 눈을 돌렸다. 성능의 규모를 늘리기 위해서 (scale), 여러 개의 코어를 마이크로 프로세서 칩에 박기 시작한 것이다. 물론 단일 칩의 성능도 꾸준히 좋아지고는 있지만, 이제 더 이상 옛날처럼 성능이라는 화폐를 마구 찍어내는 것은 아니었다. 더 이상 성능은 공짜가 아니다.

현대의 멀티코어 프로세서는 이름 대로 여러 개의 병렬 처리 코어를 담고, 복잡한 캐시 구조와, 병렬 처리를 위한 벡터 하드웨어와, 프리 페처와, 하이퍼쓰레딩, 등등 성능을 위한 많은 것들을 탑재하기 시작했다. 그리고 이런 복잡한 하드웨어의 성능을 최대한 이끌어내려면 **소프트웨어를 반드시 거기에 맞춰야 한다**. 성능을 위해 엔지니어링이 따로 필요한 것이다.

당연하지만 이런 성능 엔지니어링은 어렵다. 어떻게 하면 현대의 하드웨어를 효과적으로 활용할 수 있는 소프트웨어를 짤 수 있을까? 이것이 바로 현대 성능 엔지니어링의 핵심 질문이다.

## 행렬 곱셈 문제
성능 엔지니어링을 통해서 현대의 멀티코어 하드웨어의 성능을 어디까지 끌어낼 수 있을지, 행렬 곱셈 문제를 중심으로 살펴보자. 행렬 곱셈을 빠르게 할 수 있는 복잡도가 낮은 알고리즘이 존재하지만, 여기서는 다음과 같은 단순한 곱셈 식을 중심으로 사용할 것이다.

$$
\begin{bmatrix}
c_{11} & c_{12} & \cdots & c_{1n} \\
c_{21} & c_{22} & \cdots & c_{2n} \\
\vdots & \vdots & \ddots & \vdots & \\
c_{n1} & c_{n2} & \cdots & c_{nn} \\
\end{bmatrix}
=
\begin{bmatrix}
a_{11} & a_{12} & \cdots & a_{1n} \\
a_{21} & a_{22} & \cdots & a_{2n} \\
\vdots & \vdots & \ddots & \vdots & \\
a_{n1} & a_{n2} & \cdots & a_{nn} \\
\end{bmatrix}
\cdot
\begin{bmatrix}
b_{11} & b_{12} & \cdots & b_{1n} \\
b_{21} & b_{22} & \cdots & b_{2n} \\
\vdots & \vdots & \ddots & \vdots & \\
b_{n1} & b_{n2} & \cdots & b_{nn} \\
\end{bmatrix}
$$

$$ c_{ij} = \Sigma^{n}_{k=1} a_{ik} b_{kj} $$

문제를 심플하게 하기 위해서 $$n = 2^{12} = 4096$$ 라고 하자.

### 실험할 하드웨어
실험하기 좋은 세상이다. 클라우드가 도처에 널려있다. 가장 유명한 AWS의 c4.8xlarge 머신의 스펙은 다음과 같다. (아마도 옛날 기준인듯 하다, 지금은 스펙이 다를듯)

| 상세               | 스펙                                             |
|--------------------|--------------------------------------------------|
| 마이크로아키텍쳐   | 하스웰 (인텔 제온 E5-2666 v3)                    |
| 클럭 속도          | 2.9 GHz                                          |
| 프로세서 칩 수     | 2                                                |
| 프로세싱 코어 수   | 프로세서 칩 당 9                                 |
| 하이퍼스레딩       | 2-way                                            |
| 부동 소수점 유닛   | 각 코어가 한 사이클마다 8개의 배정밀도 연산 가능 |
| 캐시 라인 크기     | 64B                                              |
| L1 인스트럭션 캐시 | 32KB private 8-way set associative               |
| L1 데이터 캐시     | 32KB private 8-way set associative               |
| L2 캐시            | 256KB private 8-way set associative              |
| L3 캐시 (LLC)      | 25MB shared 20-way set associative               |
| DRAM               | 60GB                                             |

사실 나는 위의 하드웨어 스펙만 봐서는 이게 어떤 의미인지 잘 모르겠어서 조금 더 찾아봤다.
 * 마이크로아키텍쳐: 하스웰은 2013년에 출시했다. 강의 슬라이드 날짜인 2018년 기준으로도 최신은 아니지만, 안정적이고 전력 효율이 좋다고 한다.
 * 클럭 속도 (Clock Frequency): GHz니까 초당 29억 번 ($$ 2.9 \times 10^{9}$$) 연산(사이클)을 할 수 있다.
 * 프로세서 칩 수: 2개의 물리 프로세서 칩이 이 프로세서에 박혀있다는 뜻이다.
 * 프로세싱 코어 수: 위의 물리 칩 하나 당 9개의 코어가 있다는 뜻이다. 그래서 총 18개의 물리 코어가 있다.
 * 하이퍼스레딩: 각 물리 코어에서는 최대 2개의 쓰레드를 동시에 실행할 수 있다는 뜻이다. 그래서 총 36개의 가상 코어가 있다.
 * 부동 소수점 유닛: 원문은 "8 double-precision operations, including fused-multiply-add, per core per cycle" 이라고 되어 있는데, 이거만 봐서는 잘 이해가 안되어서 좀더 찾아봤다. 일단 FMA(Fused-Multiply-Apply) 라는 건 곱셈과 덧셈을 한 사이클에 수행하게 해주는 기능이다. 그리고 배정밀도(double-precision)는 64비트의 부동 소수점을 의미한다. "per core per cycle"라는 말이 가장 헷갈렸는데, 앞문장과 합쳐서, 이는 각각의 코어가 한 클럭 사이클마다 최대 8개의 배정밀도 연산이 가능하다는 뜻이다. 참고로 이건 **물리적으로 8개의 FPU가 달려있다는 뜻이 아니다**. 하스웰에는 AVX (Advanced Vector Extensions) 라는 명령어가 제공되는데, 이를 통해 256비트 벡터에 대한 부동 소수점 연산을 한 사이클에 처리할 수 있다. 이걸 배정밀도 기준으로 쪼개면 4개인데, FMA를 통해서 덧셈과 곱셉을 한번에 할 수 있으니, 총 8개의 배정밀도 부동 소수점 연산(그래서 모호하게 *연산* 이라고 쓴 것 같다)이 가능하다는 의미로 해석된다. 즉, 하드웨어가 제공하는 고급 연산을 통해서 각 코어마다 부동 소수점 연산의 처리량이 최대 8배 가능하다는 뜻이다. 어차피 우리는 유닛의 개수가 몇 개인지가 중요한게 아니라 처리량이 중요하기 때문에 이 정보가 더 의미있다.
 * 캐시 라인 크기: 메모리에서 한 번에 가져오는 데이터 단위이다. 이 크기만큼 캐시에 로드된다.
 * L1 캐시들: [가상 메모리 이야기](../virtual-memory)의 인트로에서 잠깐 살펴봤듯, 인스트럭션 캐시와 데이터 캐시로 나뉘어져있는 것을 알 수 있다. 32KB는 크기이고, private은 하나의 물리 코어가 독점적으로 하나 씩 갖고 있다는 의미이다. 그래서 총 18개의 L1 인스트럭션 캐시와 18개의 L1 데이터 캐시가 붙어 있다. 8-way set associative는 캐시의 주소 맵핑 방식 중 하나인데, 이건 다음 기회에 조금 더 자세히 살펴보려고 한다. 아무튼 중요한 건 매우 빠르다.
 * L2 캐시: 역시 코어마다 전용으로 붙어 있으므로 (private) 총 18개가 있고, 사이즈도 더 크지만, L1보다는 느리다.
 * L3 캐시: LLC는 Last Level Cache라는 뜻이다. 즉 여기까지만 캐시가 붙고 이후는 메모리 접근이라서 많이 느리다. shared의 기준은 칩이라서 총 2개의 L3가 붙어 있고 칩 안의 모든 9개 코어가 공유한다.

그럼 이 하드웨어 스펙으로부터 뭘 계산할 수 있냐면, 이상적인 조건에서 달성 가능한 최대 성능을 알아볼 수 있다. 특히 요즘 AI로 인해서 화두가 되고 있는 GFLOPS(기가플롭스; 초당 부동 소수점 연산의 수), 그 중에서도 이론적으로 가능한 Peak GFLOPS를 계산할 수 있다.

$$
\begin{align*}
\text{Peak GFLOPS} &= \text{클럭 속도(Hz)} \times \text{물리 코어 수} \times \text{FLOPS per Cycle} \times \text{하이퍼스레딩 팩터} \\
 &= (2.9 \times 10^9) \times 2 \times 9 \times 16 \\
 &\approx 836 \text{GFLOPS}
\end{align*}
$$

여기서 하이퍼스레딩 팩터는 하이퍼스레딩 2 way와 8배의 배정밀도 부동소수점 연산 처리량을 모두 고려한 값이다. 클럭은 초당 사이클 수 이고, 8배의 연산 처리량은 코어마다 한 사이클에 최대 8개의 배정밀도 연산이 가능하다는 의미이니 8을 곱하는 데에는 의심의 여지가 없다. 다만 2-way 하이퍼스레딩이라서 2를 곱한 것은 조금 의문이 있다. 왜냐하면 2-way 하이퍼스레딩은 물리적으로 2개의 연산 유닛이 붙어 있다는 뜻이 아니라 두 개의 논리적인 쓰레드를 동시에 실행할 수 있다는 의미라서, Peak GFLOPS를 계산할 때는 물리 코어만 고려해야하지 않나 하는게 내 생각이다. 아주 이상적인 실행 환경을 가정한다면 2를 곱하는게 맞겠지만 실제로는 달성 불가능하지 않을까 하는 생각이 있다. 아무튼 강의 슬라이드에서는 일단 2를 곱한 이상적인 값을 기준으로 했으니 여기서도 똑같이 한다.

그러면 이제 이상적인 최대 성능인 Peak GFLOPS를 기준으로, 각각의 프로그래밍 언어와 방법에 따라서 우리가 얼마나 이 하드웨어를 활용할 수 있는지 살펴보자.

### 버전 1: 파이썬

```python
import sys, random
from time import *

n = 2 ** 12

A = [[random.random() for _ in range(n)] for _ in range(n)]
B = [[random.random() for _ in range(n)] for _ in range(n)]
C = [[0 for _ in range(n)] for _ in range(n)]

start = time()
for i in range(n):
    for j in range(n):
        for k in range(n):
            C[i][j] += A[i][k] * B[k][j]
end = time()
print(f"{end - start:.6f}")
```

앞에서 봤던 행렬 곱셈에 대한 element-wise 식인 $$ c_{ij} = \Sigma^{n}_{k=1} a_{ik} b_{kj} $$ 를 나이브하게 구현한 파이썬 코드이다. 당연히 순수 파이썬이라서 느리겠지만, 이게 얼마나 느린 걸까?

위의 실험 머신에서 이걸 돌리면 21,042초, 약 6시간 정도가 걸린다고 한다. 우리는 머신의 이론적인 Peak GFLOPS가 836 이라는 사실을 계산했다. 파이썬 코드가 얻은 FLOPS를 러프하게 계산해보자.

먼저 $$n^3$$번의 반복문 안에서 곱셈과 덧셈을 하고 있으니, 총 $$ 2 \times n^3 = 2 \times (2 ^{12}) ^{3} = 2^{37} $$ 번의 부동 소수점 연산을 한다 (FLOP). 그리고 이 연산을 다 하는데 21,042 초가 걸렸으니, 최종 FLOPS는 $$ 2^{37} / 21042 \approx 6.25 \text{ MFLOPS} $$ 가 된다. Peak GFLOPS에 대한 비율을 계산해보면, 이 프로그램은 최대 성능 대비 $$ \frac{6.25 \times 10^6}{836 \times 10^9} \approx $$ **0.00078%** 밖에 뽑아내지 못한다는 사실을 알 수 있다. 순수 파이썬이 느리다는 사실은 익히 들어 알고 있지만, 이렇게 수치를 통해서 비교해보니 더더욱 처참한 수치이다.

### 버전 2: 자바

```java
import java.util.Random;

public class mm_java {
  static int n = 4096;
  static double[][] A = new doulble [n][n];
  static double[][] B = new doulble [n][n];
  static double[][] C = new doulble [n][n];

  public static void main(String[] args) {
    Random r = new Random();

    for (int i = 0; i < n; i++) {
      for (int j = 0; j < n; j++) {
        A[i][j] = r.nextDouble();
        B[i][j] = r.nextDouble();
        C[i][j] = 0;
      }
    }

    long start = System.nanoTime();
    for (int i = 0; i < n; i++) {
      for (int j = 0; j < n; j++) {
        for (int k = 0; k < n; k++) {
          C[i][j] += A[i][k] * B[k][j;]
        }
      }
    }
    long end = System.nanoTime();
    double elapsed = (end - start) * 1e-9;
    System.out.println(elapsed);
  }
}
```

역시 동일한 머신에서 수행하면, 이 자바 코드는 2,738초로 약 46분이 걸린다. 파이썬보다 7.7배는 빠르지만, 여전히 최대 성능 대비 **0.006%** 밖에 안된다.

### 버전 3: C

```c
#include <stdio.h>
#include <stdlib.h>
#include <sys/time.h>

#define n 4096
double A[n][n];
double B[n][n];
double C[n][n];

float elapsed(struct timeval *start, struct timeval *end) {
  return (end->tv_sec - start->tv_sec) + 1e-6 * (end->tv_usec - start->tv_usec);
}

int main(int argc, const char* argv[]) {
  for (int i = 0; i < n; i++){
    for (int j = 0; j < n; j++) {
      A[i][j] = (double) rand() / (double) RAND_MAX;
      B[i][j] = (double) rand() / (double) RAND_MAX;
      C[i][j] = 0.0;
    }
  }

  struct timeval start, end;
  gettimeofday(&start, NULL);
  for (int i = 0; i < n; i++) {
    for (int j = 0; j < n; j++) {
      for (int k = 0; k < n; k++) {
        C[i][j] += A[i][k] * B[k][j];
      }
    }
  }
  gettimeofday(&end, NULL);
  printf("%0.6f\n", elapsed(&start, &end));
  return 0;
}

```

Clang/LLVM 5.0 컴파일러를 이용하면 대략 1,156초로 약 19분이 걸린다. 대충 자바보다 2배, 파이썬보다 18배 빠르지만 그래도 여전히 최대 성능 대비 **0.14%**다.

여기까지는 프로그래밍 언어 간의 성능 차이를 확인할 수 있었다. 정적 타입 언어이자 머신 코드로 컴파일되어 곧바로 실행되는 C는, 동적 타입 언어이자 인터프리터를 통해 실행되는 파이썬에 비해서 18배나 빠르다. 그럼에도 여전히 우리가 계산한 이상적인 성능에는 발끝도 미치지 못한다. 그러면 이제 뭘 더 해볼 수 있을까?

### 버전 4: 반복 순서 바꾸기
가장 빨랐던 C 프로그램을 기준으로, 코드의 정확성을 희생하지 않고 반복문이 중첩되는 순서를 바꿔볼 수 있다. i, j, k 총 3개의 반복문이 있으므로 순서를 고려하면 총 6개의 반복문 순서를 얻을 수 있다. 각각을 실행해보면 다음과 같다.

| 반복 순서 (바깥쪽 -> 안쪽) | 수행 시간 (초) |
|----------------------------|----------------|
| i -> j -> k                | 1155.77        |
| i -> k -> j                | 177.68         |
| j -> i -> k                | 1080.61        |
| j -> k -> i                | 3056.63        |
| k -> i -> j                | 179.21         |
| k -> j -> i                | 3032.82        |

순서만 바꿨을 뿐인데 가장 빠른 것과 가장 느린 것의 차이가 17배나 난다!

[가상 메모리 이야기](../virtual-memory)에서 얘기했듯이, 메모리 구조는 성능에서 엄청나게 중요한 역할을 한다. 프로세서의 성능 개선의 기울기가 점점 줄어들고 있어서 멀티코어로 눈을 돌리고 있는데, 이로 인해서 성능의 병목은 연산 그 자체보다는 얼마나 효율적으로 메모리에 데이터를 올리느냐가 되었다. L1, L2, L3, 그리고 TLB 캐시까지, 모든 캐시들을 최대한으로 활용하려면, 공간 지역성을 최대한으로 하기 위해 코드에서 메모리 접근 순서를 고려해야 한다.

우리의 행렬 곱셈 케이스에서, 각 행렬은 메모리에 행 우선 순서 (row-major order) 로 올라가있다. 즉, 다음과 같은 행렬이 있을 때:

$$
\begin{bmatrix}
Row 1 (= x_{1,1} x_{1,2} \cdots x_{1,N})\\
Row 2 (= x_{2,1} x_{2,2} \cdots x_{2,N})\\
\cdots \\
Row N (= x_{N,1} x_{N,2} \cdots x_{N,N})\\
\end{bmatrix}
$$

이 행렬은 메모리에 다음과 같은 연속된 모양으로 올라간다.

$$
\begin{bmatrix}
Row 1 & Row 2 & \cdots & Row N
\end{bmatrix}
$$

그러면 우리가 처음에 구현했던 순서인 i -> j -> k (1155.77초)를 다시 살펴보자.
```c
for (int i = 0; i < n; i++)
  for (int j = 0; j < n; i++)
    for (int k = 0; k < n; k++)
      C[i][j] += A[i][k] * B[k][j];
```
 * C: 어차피 제일 안쪽 반복문(k) 안에서 접근하는 C의 원소는 한 군데 (i, j) 뿐이다. 공간 지역성이 아주 좋다.
 * A: A[i] 행에 대해서 0부터 k까지 순차적으로 접근한다. 공간 지역성이 좋다.
 * B: 공간 지역성이 최악이다. B[0] 번째 행의 j번째 원소부터, B[k] 번째 행의 j번쨰 원소까지 접근해야 한다. 그러면 B[0][j]에 접근한 후 B[1][j]에 접근하려면 4096개의 연속된 블럭 메모리를 뛰어넘어가야 한다.

제일 빨랐던 i -> k -> j (117.68초) 는 어떨까?
```c
for (int i = 0; i < n; i++)
  for (int k = 0; k < n; i++)
    for (int j = 0; j < n; k++)
      C[i][j] += A[i][k] * B[k][j];
```
 * C: 이제 가장 안쪽 반복문은 j다. C[i] 번째 행의 0부터 j번째 원소까지 접근하므로 공간 지역성이 훌륭하다.
 * A: 가장 안쪽 반복문 j에서 접근하는 A의 원소는 (i, k) 한 군데 뿐이다. 최고다.
 * B: 이제 B의 공간 지역성도 훌륭하다. B[k] 번째 행의 0부터 j번째 원소까지를 순차적으로 접근한다.

말이 되는 설명이다. 그러면 실제로는 어떨까? 모든 성능 엔지니어링은 수치를 직접 눈으로 확인하는 프로파일링 과정이 필수적이다. 캐시의 효과를 살펴보기 위해서는 우리는 `valgrind` 프로그램에 `--tool=cachegrind` 옵션을 줘서, 캐시의 성능을 시뮬레이션해볼 수 있다[^1].

[^1]: 캐시 성능을 측정하는 게 아니라 시뮬레이션하는 이유는 하드웨어의 복잡성으로 인한 한계 때문이다. 실제 CPU의 성능 카운터로는 모든 캐시 동작을 정확하게 기록할 수 없고, 기타 복잡한 맥락들, 예를 들어 prefetch, speculation 등의 하드웨어 간섭과 OS, 백그라운드 프로세스 등의 소프트웨어 간섭으로 인해서 측정이 불가능한 것들이 있다. 그래서 Cachegrind는 프로그램을 직접 실행하긴 하면서 가상의 캐시 모델을 기반으로 캐시 동작을 시뮬레이션 한다. 프로그램의 모든 메모리 접근을 추적하고, 이게 진짜 캐시에 어떻게 반영될지를 계산하는 것이다.

참고로 Cachegrind는 L1, L2, L3의 여러 개의 캐시 중 LL (Last Level)을 중심으로 캐시 미스율을 계산한다[^2].

[^2]: 실제로는 L1, L2, L3를 모두 시뮬레이션 하지만, CPU와 메인 메모리 상
