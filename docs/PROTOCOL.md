# 시리얼 프로토콜

USB CDC 시리얼, **115200 8N1**. 호스트→보드 명령은 한 줄(`\n` 종료) 단위.

## 보드 → 호스트

### 부팅 배너
```
IR ready v1.1.0: RX=GP0, TX=GP15 (38000Hz). Press a remote, or send 'TX:carrier:csv' / 'VER?'.
```

### 캡처 출력 (리모컨 학습)
리모컨 버튼을 수신부에 쏘면 프레임마다 출력:
```
# NEC raw=0xF609E710 addr=0xE710 cmd=0x09 ok      ← NEC 디코딩 시에만(옵션)
RAW(38000): 9000,4500,560,560,560,1690,560, ...   ← 항상
```
- `RAW(<carrier>): <csv>` — 엣지 간 간격(µs) 목록. **첫 값 = 캐리어 ON(리더 mark)**, 이후 ON/OFF 교대.
- 이 값을 그대로 발신(`TX:`)하거나 안드로이드 `ConsumerIrManager.transmit(carrier, pattern)` 에 넣으면 됨.

## 호스트 → 보드 (명령)

| 명령 | 응답 | 설명 |
|---|---|---|
| `VER?` | `VER:1.1.0` | 펌웨어 버전 |
| `INFO?` | `INFO:name=ZBD IR Board;ver=1.1.0;rx=GP0;tx=GP15` | 보드 정보 |
| `TX:<carrier>:<µs csv>` | `OK` / `ERR:<msg>` | 적외선 발신 |

### TX 예시
```
TX:38000:9000,4500,560,560,560,1690,560,560,560,1690,560
```
- `<carrier>`: 반송파 Hz (보통 38000)
- `<µs csv>`: ON/OFF 지속시간(µs) 목록, 첫 값 ON(mark)부터 교대
- 응답 `OK` 까지 ≈ 패턴 송출시간(예: NEC 1프레임 ~68ms) — 폰 IR과 동일

### 에러
- `ERR:short` — 패턴이 2개 미만
- `ERR:<예외메시지>` — 파싱/송신 실패

## 타이밍 / 정확도
- 발신은 PWM 38kHz(듀티 ~33%) + µs 비지웨이트로 각 구간 송출. NEC 등 일반 리모컨 허용오차 내.
- 더 높은 정밀도가 필요하면 RP2040 PIO 기반 송신으로 교체 가능(펌웨어 수정).

## 구현 메모
- 메인 루프: 논블로킹 `select.poll(sys.stdin)` 으로 명령 1줄(`readline`) 읽기 + 캡처 emit.
- 명령은 `readline` 통째 읽기라 긴 `TX:` 라인도 즉시 처리(폰 IR급 반응속도).
