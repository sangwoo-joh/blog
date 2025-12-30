---
layout: post
tags: [cs, life]
published: true
title: Emacs Native Compliation
subtitle: Official!
---

 몰랐는데 Andrea Corallo 님께서 작업하신 이맥스 native compilation
 브랜치가 [master 브랜치에 머지되었다는
 소식](https://www.reddit.com/r/emacs/comments/myej3z/the_nativecompilation_branch_was_just_merged_into/)을
 보았다. GNU 로그를 보니
 [진짜](https://git.savannah.gnu.org/gitweb/?p=emacs.git;a=commit;h=289000eee729689b0cf362a21baa40ac7f9506f6)다. 당장 써보자.

 일단 `configure` 옵션이 [기존 feature 브랜치](emacs-native-comp)와 좀
 달라졌다: `./configure --with-native-compilation` 을 해야
 한다. 나머지는 똑같다. GCC-10과 libgccjit 디펜던시를 설치하고 CC와
 CXX를 적절하게 설정해둔 뒤 `./autogen.sh` 후 `./configure
 --with-native-compilation` 하고 빌드하면 된다. 그런데 `master`
 브랜치를 곧바로 시도했더니 빌드 실패가 뜬다(?). 아마 다른 기능들까지
 반영되어서 내 로컬에서는 빌드가 깨지는 듯 하다. 침착히 찾아보니
 `emacs-28.0.50` 기준으로 반영이 된 것 같다. `tag`를 보니
 `emacs-28.0.90`, `emacs-28.0.91`, `emacs-28.0.92`가
 있었다. 흐음. `emacs-28.0.92`를 빌드 시도해보았다. 안된다. `make`로
 병럴 작업 없이 시도해보았다. 안된다. `emacs-28.0.90`으로
 시도해보았다. `make -j5`로 잡을 5개나 주었는데 대략 8분정도 걸려서
 빌드에 성공하였다.

 빌드 후 인스톨해서 켜보니 예상과는 다르게 엄청나게 오랜 시간 동안
 로딩을 진행하였다. 뭐 때문인지 `htop`으로 작업을 살펴보니 기존에
 빌드해둔 `eln` 들을 싹 무시하고 처음부터 새로 다시 빌드하고
 있었다. 그럴 수 있지. 적절한 시간이 흐르고 네이티브 컴파일레이션이
 끝나고 나니 다시 원래의 이맥스로 돌아왔다. 이미 네이티브를 쓰고
 있어서 크게 체감은 안되지만, 정식으로 메인 브랜치에 반영되었으니 이제
 안심하고 써도 되겠다. 레딧 댓글을 보니 28 공식 버전에는 디폴트로
 네이티브가 들어간다고 하는데 기대된다.
