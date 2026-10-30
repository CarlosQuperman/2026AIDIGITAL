# 처리 기록 (예시)

- 실행: 2026. 11. 2.(월) 기준, gongmun-organizer → todo-extractor → weekly-report
- 1단계: input/ 10건 읽음 (hwpx 6건, pdf 4건) · 실패 0건
  - 저장: work/공문목록.json, output/공문목록.xlsx
- 2단계: 이번 주 4건, 다음 주 4건, 그 이후 2건, 확인 필요 0건
  - 저장: output/이번주_할일.md
- 3단계: 업무1~8 = 마감 임박 8건, 다음주1~2 = 11. 20., 11. 27. 마감 2건
  - 저장: output/주간업무보고.hwpx (작성자 칸은 사람이 고칠 것)
