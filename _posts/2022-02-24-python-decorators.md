---
layout: post
tags: [cs]
published: true
title: 파이썬 데코레이터
---

 요즘 파이썬으로 다양한 작업을 하고 있다. 덕분에 동적 타이핑
 세계에서만 해볼 수 있는 다양한 짓(?)을 해보고 있는데, 그 중에서도
 데코레이터를 유용하게 썼던 경험을 소개해본다.

## 파이썬 데코레이터
 데코레이터의 생긴 모습 자체는 익숙하다. 자바에도
 [어노테이션](https://en.wikipedia.org/wiki/Java_annotation)이라는게
 있긴 한데, 얘는 정적인 용도로 컴파일 타임에 주로 쓰이는 것으로 알고
 있다. 반면 파이썬의 데코레이터는 동적인 환경에서 온갖 다양한 훅을
 구사할 수 있다. 생긴 모습은 다음과 같다.

```python
@decorator
def foo(x):
    return x
```

 `@`로 시작하는 부분이 함수에 씌여진 데코레이터이다. 적용된 함수의
 **모든 것**을 동적으로 후킹할 수 있는데, 예를 들면
  - 함수가 속한 클래스, 함수 이름
  - args와 kwargs를 포함한 모든 함수 아규먼트들
  - 아예 함수 자체를 호출하지 않거나 두 번 이상 호출할 수도 있다.

 그러니까 함수의 행동을 동적으로 조작하고 싶을 때 유용한 것으로
 이해했다.

 모든 것이 오브젝트로 관리되는 파이썬 세계에서 사실 데코레이터 역시
 [그냥
 함수](https://www.python.org/dev/peps/pep-0318/#motivation)다. 그러니까
 위의 코드는 사실 아래와 같다.

```python
def decorator(func_to_wrap):
    def closure(*args, **kwargs):
        return func_to_wrap(*args, **kwargs)

    return closure

# apply decorator
foo = decorator(foo)
```

 함수도 오브젝트이므로 파라미터로 넘길 수 있는데(functional?!), 이를
 받아서 원래 함수와 원래 아규먼트를 가지고 다양한 짓을 하는
 클로저(`closure`)를 만들어서 리턴하는 함수가 바로
 데코레이터다. 여기서는 그냥 원래 함수를 원래 아규먼트로
 호출했다. `@decorator`는 데코레이터를 감싸서 만든 클로저 `foo =
 decorator(foo)`를 좀더 읽기 좋게 만들어주는 Syntactic Sugar다.

 코드를 보면 알겠지만 `foo`에 넘어가는 모든 파라미터들을
 `closure(*args, **kwargs)`로 후킹하고 있기 때문에 우리는 이 모든
 파라미터들에 접근할 수 있게 된다.


## `functools.wraps`
 다만 위와 같이 클로저를 만들어 버리면 한 가지 문제가 생긴다. 원본
 함수 `foo`를 받아서 이걸 클로저로 덮어 쓴 함수 오브젝트를 리턴하기
 때문에, 데코레이팅된 `foo` 함수 오브젝트를 `print`로 찍어보면 이름이
 `foo`가 아니라 `closure`가 나온다.

```python
<function decorator.<locals>.closure at ....>
```

 생각해보면 당연하다. 우리는 원본 `foo` 함수를 돌려준게 아니기
 때문이다. 앞에서 모든 것을 후킹할 수 있다고 했는데, 이러면 함수
 이름이나 함수가 속한 클래스를 못찾게 된다. 여기서는 함수 이름을
 예시로 들었지만, 실제로는 원본 함수 오브젝트의 모든 함수 관련
 속성(function attribute), 즉 `__name__`, `__dict__`, `__qualname__`,
 `__code__`, `__module__`, `__doc__` 등을 잃어버리게 된다.

 이 문제를 해결해주는 아이가 바로 `functools.wraps`이다. 얘는 표준
 라이브러리에 있으니까 맘 편히 쓰면 된다. 사용 방법은 위의 데코레이터
 정의에 다음 한 줄을 추가해주면 된다.

```python
import functools

def decorator(func_to_wrap):
    @functools.wraps(func_to_wrap)
    def closure(*args, **kwargs):
        return func_to_wrap(*args, **kwargs)

    return closure
```

 한마디로 정확한 데코레이터를 만들기 위한 데코레이터다. 뭔가 점점
 게슈탈트 붕괴가 일어나는 듯 하다. 아무튼 얘는 파라미터로 받은 원본
 함수 오브젝트의 모든 메타데이터를 유지해준다. 구체적으로는
 `update_wrapper`와 `parital` 등 깊은 내부 구현 사항이 있는데 거기까지
 알아야 할 일은 없을 것 같아서 이쯤에서 멈추겠다.

 아무튼 **데코레이터를 만들 때는 `functools.wraps`로 원본 함수를 한번
 감싸 줘야 함수 속성이 유지된다**는 것만 기억하면 된다.

## 유용하게 썼던 데코레이터
### 타이머
 먼저 타이머다. 이름 그대로 함수에 타이머를 달아서 수행 시간을 측정할
 수 있다.

```python
import time
import datetime
import functools

def timer(func):
    @functools.wraps(func)
    def closure(*args, **kwargs):
        started = time.time()
        res = func(*args, **kwargs)
        finished = time.time()
        time_spent = datetime.timedelta(seconds=(finished - started))
        print(f"{func.__qualname__} took {time_spent}")
        return res

    return closure
```

 - `time.time()`으로 원본 함수 전후에 틱을 잰다. 단위는 초(second)다.
 - `datetime.timedelta()`로 시간 간격을 읽기 좋은 형태로 바꿔서
   출력한다.
 - `__qualname__` 속성으로 수행한 함수 이름(메소드라면 클래스
   이름까지) 같이 보여주면 좋다.
 - 참고로 `*args`에 `self`까지 같이 넘어오기 때문에, 이거 하나로 일반
   함수 및 클래스의 메소드까지 다 적용할 수 있다.

 여기서 좀더 나가면 `*args` 또는 `**kwargs`에 특정 타입의 오브젝트가
 넘어온다고 가정하고, 해당 오브젝트의 특정 필드에 함수 수행 시간을
 기록할 수도 있다. 나는 보통 장고의 ORM 오브젝트를 넘겨서
 `time_spent`를 저장하기도 했다.

### 예외 삼키기
 많은 API를 호출해서 결과 페이로드를 파싱해야 할 때가 있다. 그런데
 오래 서비스된 API라서 페이로드의 모양이 일정하지 않은 경우가 종종
 있다. 즉, 서버의 버전이 업그레이드되면서 Json의 특정 필드가 `null` 인
 경우가 생기는 것이다. 이런 코너 케이스를 모두 일일이 찾아서 그에
 해당하는 디폴트 값을 줘도 되지만, 단순하게 특정 필드가 `null`인
 경우를 아예 무시해도 좋은 경우라면 그냥 예외를 삼켜버리면 된다. 보통
 다음 예외가 발생한다:
  - `TypeError`: `null` 오브젝트에 인덱스로 접근할 때 발생한다. 즉
    `None[1]`에서 발생한다.
  - `KeyError`: 오브젝트 자체는 `null`이 아니지만 키 값이 없을 때
    발생한다. 즉 `{'a': 1}['b']`에서 발생한다.
  - `AttributeError`: 속성 자체가 없을 때 발생한다. 예를 들어 어떤
    클래스의 인스턴스 `foo`에 `foo.a`는 있는데 `foo.b`는 없으면
    발생한다.

 사실 모든 예외를 싸그리 `Exception`으로 잡아서 무시해도 되지만,
 그러면 다른 오류가 난 경우까지 삼켜버리기 때문에 나중에 괴상한 오류를
 만날 수도 있으니 주의해야 한다. 아무튼 이렇게 집어 삼킬 예외를
 정의하고 나면 다음과 같은 데코레이터를 사용할 수 있다.

```python
import functools

def swallow_exception(func):
    @functools.wraps(func)
    def closure(*args, **kwargs):
        try:
            res = func(*args, **kwargs)
        except (TypeError, KeyError, AttributeError):
            res = None
        return res

    return closure
```

 별거 없이 `try ... except`로 한번 감싸서 원하는 예외만 삼키는
 구조인데, 내가 겪은 것처럼 예외가 여기저기 발생할 수 있어서 여기저기
 `try`를 삽입하기 귀찮을 때 유용하게 쓸 수 있다.

## 데코레이터 적용 순서
 앞에서 데코레이터는 그냥 클로저를 리턴하는 함수라고 했는데, 따라서
 당연히 하나의 함수에 여러 개의 데코레이터를 적용하는 것도
 가능하다. 그리고 파이썬 표준에서는 이렇게 여러 개의 데코레이터가
 적용됐을 때 [어떤 순서로
 적용되는지](https://mail.python.org/pipermail/python-dev/2004-September/048874.html)를
 명시하고 있는데, 한마디로 **함수에 가까운 것부터 먼저
 적용**된다. 코드를 위아래로 훑는다고 생각하면 일종의 스택이라고
 생각해도 되겠다. 맨 마지막(아래) 데코레이터부터 적용되니까.

 아래와 같이 위의 두 가지 데코레이터를 두 가지 순서로 적용한 경우를
 모두 살펴보자.

```python
# swallow_exception -> timer
@timer
@swallow_exception
def bar():
    raise TypeError


# timer -> swallow_exception
@swallow_exception
@timer
def baz():
    raise TypeError
```

 - `bar()`를 호출하면 `@swallow_exception`가 먼저 예외를 삼키고, 그
   다음 `@timer`가 앞선 모든 동작의 시간을 계산하여 출력한다.
 - 반면 `baz()`를 호출하면 `@timer`가 먼저 적용되는데, 예외가 발생하여
   시간 계산을 끝내지 못하고 예외를 던져버린다. 그러면
   `@swallow_exception`이 던져진 예외를 삼키게 되고 결과적으로 아무런
   출력이 없다.

---

 정적 타입과 함수형 프로그래밍 지지자로서 파이썬 관련 글은 피하고
 싶었지만, 파이썬으로 밥 벌어 먹고 살다 보니 이쪽의 경험이 유의미하게
 늘어나고 있고 개중에는 또 재밌고 유용한 것도 있어서 이렇게 기록을
 남기게 되었다. 기왕 이렇게 된 거 종종 파이썬 관련 글도 써봐야겠다.
