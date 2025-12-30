---
layout: post
tags: [cs]
title: 리-다이렉션
subtitle: 저리 가라
published: true
---

분석 시간 관련 이슈를 파기 위해 빌드에 최소 8분, 최대 50분 정도 걸리는 패키지들을 빌드해보고 있었다. 빌드 도중에 떨어지는 부가 데이터와 각각 패키지들의 빌드 시간도 기록할겸 대충 `time build_cmd > log` 때리고 퇴근했다. 그런데 오늘 와서 보니 log 파일에는 빌드 관련 로그만 잔뜩 남아있고 `time` 커맨드의 실행 결과는 터미널에만 남아있는 것이 아닌가? 당연히 시간도 남을 거라 생각해서 좀 당황했지만 관련 내용을 찾아보니 금방 이유를 찾을 수 있었다.

결론부터 말하면 `time` 커맨드를 쓰지말고 `\time` 커맨드와 `-v` , `-o filename` 옵션을 이용해서 시간과 메모리 사용량 모두 파일에 쓰고 광명을 찾는 것이 좋다.


### time 커맨드
man 페이지를 보면 다음 설명이 있다.

> **DESCRIPTION**
>
> **time** run the program _COMMAND_ with any given arguments _ARG..._. When _COMMAND_ finishes, **time** displays information about resources used by _COMMAND_ (on the standard error output, by default). If _COMMAND_ exits with non-zero status, **time** displays a warning and the exit status.

주목해야 하는 부분은 `on the standard error output, by default`이다. 즉 time 커맨드의 결과는 stdout이 아니라 stderr에 쓰이고 있었던 것이다. (man 페이지 읽는 습관을 생활화합시다...)


### 리다이렉션
[링크](https://en.wikipedia.org/wiki/Redirection_(computing))의 내용 중 일부를 발췌해왔다.

유닉스 쉘의 i/o stream은 다음과 같다.

| 핸들 | 이름   | 설명            |
|------|--------|-----------------|
| 0    | stdin  | Standard input  |
| 1    | stdout | Standard output |
| 2    | stderr | Standard error  |

예를 들어, `command1 2> file1`은 `command1`을 실행하고, 표준 에러 스트림을 `file`에다 쓰게 된다. csh 계열의 쉘에서는 i/o 스트림을 구분하기 위해 숫자 앞에 `&`를 붙이는데, 이유는 `1`이라는 파일과 표준 출력 `1`을 구분하기 위해서다. 그래서 `cat file 2>1`의 경우는 stderr이 `1`이라는 이름의 파일에 리다이렉트되고, `cat file 2>&1`의 경우는 stderr이 stdout에 리다이렉트된다.

또하나 쓸만한 것은 표준 파일 핸들을 다른 파일로 리다이렉트 하는 것이다. 가장 유명한 건 역시 stderr를 stdout에 합쳐서 에러메시지를 같이 처리하는 일이다. 예를 들어, `find / -name .profile > results 2>&1` 커맨드는 파일이름이 `.profile`인 모든 파일을 찾아서 그 결과를 `result` 파일에다 쓴다. 리다이렉션 없이 실행하면, 찾은 건 stdout에 출력하고 에러(예를 들면, 보호된 디렉토리를 탐색하려고 할때 발생하는 권한 오류)는 stderr에 출력한다. 즉, stdout이 `results` 파일에 출력되는 반면, 에러메시지는 그냥 콘솔에 출력되는 것이다. 찾은 것과 에러 메시지 둘 다 `results` 파일에다 쓰고 싶으면, `2>&1`을 이용해서 stderr(핸들 2)를 stdout(핸들 1)에 합치면 된다.

만약에 합친 출력을 파이프로 다른 프로그램에 던져 주고 싶으면, `2>&1`로 머지한 시퀀스가 파이프에 넘겨 주기 전에 앞서야 한다. 즉, `find / -name .profile 2>&1 | less` 꼴이 되야 한다.

`command > file 2>&1`은 다음과 같이 해석하면 된다. 먼저 표준 출력(`command`의 정상 실행 결과)이 `file`로 리다이렉트된다. 그리고 stderr이 추가적으로 stdout 핸들로 리다이렉트되는데, 이때 이미 stdout은 `file`로 리다이렉트된 상황이다. 따라서 최종적으로 `command`의 실행 결과와 오류가 모두 `file`에 쓰여진다.
