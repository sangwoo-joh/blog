---
layout: post
title: Insertion and Merge Sorts
tags: [cs]
last_update: 2024-01-15 18:10:49
---

# 삽입 정렬과 병합 정렬

```c++
void insertionSort(int* arr, int from, int to) {
  for (int i = from; i < to; i++) {
    int tempVal = arr[i + 1];
    int j = i + 1;
    while (j > from && arr[j - 1] > tempVal) {
      arr[j] = arr[j - 1];
      j--;
    }
    arr[j] = tempVal;
  }
}
```

```c++
void merge(int* arr, int p, int q, int r) {
  int n1 = q - p + 1;
  int n2 = r - q;
  int left = new int[n1];
  memcpy(left, arr + p, sizeof(int) * n1);
  int right = new int[n2];
  memcpy(right, arr + q + 1, sizeof(int) * n2);

  int ri = 0, li = 0;
  for (int i = p; i < r - p + 1; i++) {
    if (ri == n2) {
      arr[i] = left[li++];
    } else if (li == n1) {
      arr[i] = right[ri++];
    } else if (right[ri] > left[li]) {
      arr[i] = left[li++];
    } else {
      arr[i] = right[ri++];
    }
  }
}
```

```c++
void sort(int* arr, int p, int r) {
  static const int k = 10;
  if (r - p > k ) {
    int q = (p + r) / 2;
    sort(arr, p, q);
    sort(arr, q + 1, r);
    merge(arr, p, q, r);
  } else {
    insertionSort(arr, p, r);
  }
}
```
