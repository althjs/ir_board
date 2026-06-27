# ZBD IR Board — 오픈소스 IR 학습/발신 보드 펌웨어

RP2040(Raspberry Pi Pico / Pico-Zero 등) 기반의 **적외선(IR) 리모컨 학습·발신** 펌웨어입니다.
리모컨 신호를 캡처해 JSON으로 저장하고, 폰/PC에서 다시 발신할 수 있게 해주는 만능 리모컨용 동반 하드웨어예요.

> **[즈비드 만능 리모컨](https://zbd.kr/ir)** 앱/웹과 함께 동작합니다.
> 펌웨어·하드웨어는 오픈소스(MIT) — 직접 만들고 플래시해서 쓰셔도 됩니다.

```
[실제 리모컨] ──학습──▶ [보드 RX(GP0)]  ──USB 시리얼──▶  PC(웹) / 폰(앱)
                                                            │
[TV·에어컨·스피커] ◀──발신── [보드 TX(GP15)] ◀──"TX:..."──┘
```

---

## ✨ 기능
- **수신(학습)**: IR 리모컨 신호를 µs 단위 RAW 타이밍으로 캡처, NEC 디코딩 라벨 제공
- **발신**: 38kHz(가변) 반송파로 RAW 패턴 송출 — 폰에 IR이 없어도 USB 보드로 발신
- **USB 시리얼 한 줄 프로토콜** — 웹(Web Serial)/안드로이드(USB host) 어디서나 동일
- 펌웨어 버전 보고(`VER?`/`INFO?`)
- 의존성 없음 — MicroPython만 있으면 동작

## 🧩 하드웨어
| 용도 | 부품 | 핀 |
|---|---|---|
| 보드 | RP2040 (Pico / Pico-Zero 등) | USB |
| IR 수신 | VS1838B/TSOP 류 3핀 모듈 | OUT→**GP0**, VCC→3V3, GND→GND |
| IR 발신 | IR LED + NPN 트랜지스터 (또는 KY-005류 모듈) | DAT→**GP15**, VCC→**5V**, GND→GND |

- **폰 발신 전용**이면 수신부 없이 발신부(GP15)만 있으면 됩니다.
- 자세한 배선/부품: **[docs/HARDWARE.md](docs/HARDWARE.md)**

## 🚀 빠른 시작 (플래시)

### 1) MicroPython 설치
1. 보드의 **BOOT 버튼**을 누른 채 USB 연결 → `RPI-RP2` 드라이브가 뜸
2. [micropython.org/download](https://micropython.org/download/RPI_PICO/) 에서 **RPI_PICO** `.uf2` 다운로드
3. `.uf2` 를 `RPI-RP2` 드라이브에 끌어다 놓기 → 자동 재부팅

### 2) 펌웨어(main.py) 올리기 — 가장 쉬운 방법: [Thonny](https://thonny.org)
1. Thonny 실행 → 우하단에서 인터프리터 **MicroPython (Raspberry Pi Pico)** 선택
2. `firmware/main.py` 를 열고 → **File ▸ Save as ▸ Raspberry Pi Pico** → 이름 `main.py`
3. 보드 재부팅(USB 재연결) → 끝

> 명령행 도구가 익숙하면 [`mpremote`](https://docs.micropython.org/en/latest/reference/mpremote.html): `mpremote connect <port> fs cp firmware/main.py :main.py`

### 3) 동작 확인
- 시리얼 터미널(115200)에서 보드가 `IR ready v1.1.0: RX=GP0, TX=GP15 ...` 출력
- 리모컨을 수신부에 대고 누르면 `RAW(38000): 9000,4500,...` 가 떠야 정상
- 또는 **[zbd.kr/ir/debug](https://zbd.kr/ir/debug)** 에서 보드 연결해 시각적으로 확인

## 🔌 시리얼 프로토콜 (115200 8N1)
| 방향 | 내용 |
|---|---|
| 보드→호스트 | 캡처 시 `# NEC raw=0x...` (옵션) + `RAW(<carrier>): <µs csv>` |
| 호스트→보드 | `VER?` → `VER:1.1.0` |
| | `INFO?` → `INFO:name=ZBD IR Board;ver=1.1.0;rx=GP0;tx=GP15` |
| | `TX:<carrier>:<µs csv>` → 발신 후 `OK` (실패 `ERR:...`) |

자세한 규격: **[docs/PROTOCOL.md](docs/PROTOCOL.md)**

## 🛠 앱/웹과 함께 쓰기
- **PC(웹)**: Chrome/Edge에서 [zbd.kr/ir](https://zbd.kr/ir) → "보드 연결"(Web Serial) → 캡처/발신
- **안드로이드 앱**: IR 없는 폰에 USB-OTG로 보드 연결 → 앱이 발신을 보드로 라우팅
- 둘 다 위 시리얼 프로토콜만 쓰므로, **직접 만든 도구**로도 제어 가능합니다.

## 📦 부품 구하기
RP2040 보드 + IR 수신모듈 + IR LED/트랜지스터 — 합쳐서 몇 천 원이면 구성됩니다.
조립이 번거로우면 [즈비드](https://zbd.kr) 후원 시 키트 발송도 받을 수 있어요. (수신전용 / 수신+발신)

## 📄 라이선스
[MIT](LICENSE) — 펌웨어·문서 자유롭게 사용/수정/배포하세요.

## 🔗 링크
- 웹 캡처 도구: https://zbd.kr/ir
- 보드 디버그: https://zbd.kr/ir/debug
- 문의: althjs@gmail.com
