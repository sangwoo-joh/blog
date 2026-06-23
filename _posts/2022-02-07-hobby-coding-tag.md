---
layout: post
tags: [other]
published: true
title: 태그 추가
---

 취미 코딩의 일환으로 [태그 기능](https://github.com/sangwoo-joh/blog/commit/6295328cf05b366d46d712d5a1929dc9ab845abc)을 추가하였다. 기존의 `/usr`와 `/dev`의 이단 분류도 괜찮았지만 너무 Coarse해서 다양한 글을 분류하기 어렵다는 문제는 늘 인식하고 있었는데, 마침 [Jekyll에 태그 추가하기](https://wormwlrm.github.io/2019/09/22/How-to-add-tags-on-Jekyll.html)라는 글을 흘러흘러 읽고 단숨에 만들어버렸다. 자바스크립트와 css 몇 줄로 추가한 거라 화려하진 않지만 태그 본연의 기능은 충실히 수행하고 있다고 본다.

 이제 남은 것은 최근 1주일 이내 포스트 앞에 `new!`를 동적으로 붙여주는 것과, 태깅을 book 에도 적용하는 일이다. 대충 어떻게 할지는 머릿속에 그려놓았으니 미래의 나한테 맡겨둔다.

---
#### 2022/02/08 업데이트
 [`new!` 붙이기](https://github.com/sangwoo-joh/blog/commit/276090ec4ec4c39ba05213173578b8b363ceee8f)와 [book 태깅 적용](https://github.com/sangwoo-joh/book/commit/5c50ad5285c54ba3b8092e24a10b60ddd370fea5)을 모두 마쳤다. 이게 가장 좋은 방법인지는 모르겠지만 구현하는 동안 재밌었다. 특히 book 태그 페이지에서 [태그 별 포스트 개수를 세는 기능](https://github.com/sangwoo-joh/book/commit/cc3015080375cd6288d2bfeeb8ff8b50f16f43b2)을 만들 때는 HTML, 지킬의 리퀴드 템플릿과 데이터, 바닐라 자바스크립트, jQuery를 전부 다 쓰게 되었는데, 이게 가장 좋은 방법인지는 모르겠으나 요리조리 블록을 껴 맞추는 느낌이라 즐겁게 했다. 다만 느낀 점은 이런 작은 블로그에서는 저런 흑마법스러운 코드를 짜도 괜찮지만, 규모가 조금만 커져도 이런 식으로는 관리가 안될 것이라는 확신이 있었다. 그래서 리액트나 앵귤러가 나왔고 그걸로도 부족해서 타입스크립트와 리스크립트가 발전하고 있는 것 아닐까 하는 개인적인 생각이 들었다.
