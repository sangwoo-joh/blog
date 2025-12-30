---
layout: post
tags: [idea, cs]
published: true
title: 1조짜리 실수
---

>  I call it my billion-dollar mistake. It was the invention of the null reference in 1965. At that time, I was designing the first comprehensive type system for references in an object oriented language, ALGOL W. My goal was to ensure that all use of references should be absolutely safe, with checking performed automatically by the compiler. But I couldn't resist the temptation to put in a null reference, simply because it was so easy to implement. This has led to innumerable errors, vulnerabilities, and system crashes, which have probably caused a billion dollars of pain and damage in the last forty years. - Tony Hoare, Speaking at a conference in 2009, QCon

글쎄. 말은 저렇게 했지만 사실 저 당시에는 최선의 선택 아니었을까?
