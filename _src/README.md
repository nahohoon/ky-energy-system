# 스마트 에너지 운영관리 시스템 (KY Energy Management System)

> 본 시스템은 콤프레샤 설비 운영데이터와 유지보수 이력, 부품 재고를 통합 관리하고,
> 에너지 절감 가능성을 시뮬레이션하여 고객의 운영 효율과 비용 절감을 동시에 지원하는
> **스마트 에너지 운영관리 시스템**입니다.

---

## 📌 주요 기능

| 모듈 | 기능 |
|------|------|
| 🏠 대시보드 | KPI 카드, 설비별 전력사용 차트, 월별 절감액 추이, 최근 운전로그/정비이력 |
| ⚙️ 설비관리 | 설비 등록/수정/삭제, 상태관리(가동중/점검중/정지), 설비 상세 페이지 |
| 📊 운전데이터 | 설비별 일별 운전로그(가동시간, 전력, 부하율, 압력, 주파수) 관리 |
| ⚡ 에너지분석 | 설비별 효율비교, 절감가능량, 예상절감금액, 월별 추이 차트 |
| 💡 절감시뮬레이션 | 기존vs개선 전력 비교, 절감량/절감금액/CO₂ 자동계산 |
| 🔧 정비관리 | 정비이력 등록, 다음점검일 알림(D-day), 임박 점검 경고 |
| 📦 부품재고관리 | 부품 등록, 입출고 처리, 안전재고 경고, 입출고 이력 |

---

## 🛠 기술 스택

- **Backend**: Python Flask + SQLAlchemy
- **Database**: SQLite
- **Frontend**: Bootstrap 5.3 + Chart.js 4
- **Template Engine**: Jinja2

---

## 📁 프로젝트 구조

```
ky_energy_system/
├── app.py              # Flask 앱 팩토리
├── config.py           # 환경설정
├── models.py           # DB 모델 (8개 테이블)
├── init_db.py          # DB 초기화 + 더미데이터
├── routes/
│   ├── dashboard.py    # 대시보드
│   ├── equipment.py    # 설비관리
│   ├── operation.py    # 운전데이터
│   ├── energy.py       # 에너지분석
│   ├── simulation.py   # 절감시뮬레이션
│   ├── maintenance.py  # 정비관리
│   └── inventory.py    # 부품재고관리
├── templates/
│   ├── base.html       # 공통 레이아웃 (사이드바 + 상단바)
│   ├── dashboard/
│   ├── equipment/
│   ├── operation/
│   ├── energy/
│   ├── simulation/
│   ├── maintenance/
│   └── inventory/
└── static/
    ├── css/
    └── js/
```

---

## 🚀 실행 방법

### 1. 패키지 설치
```bash
pip install flask flask-sqlalchemy
```

### 2. DB 초기화 (더미데이터 포함)
```bash
python init_db.py
```

### 3. 서버 실행
```bash
python app.py
```

### 4. 브라우저 접속
```
http://localhost:5000
```

---

## 🗄 DB 테이블 구조

| 테이블 | 설명 |
|--------|------|
| `companies` | 회사/고객사 정보 |
| `equipments` | 설비 기본 정보 |
| `operation_logs` | 설비별 운전 데이터 |
| `energy_analysis` | 월별 에너지 분석 결과 |
| `saving_simulations` | 절감 시뮬레이션 시나리오 |
| `maintenance_logs` | 정비 이력 |
| `parts` | 부품 마스터 |
| `inventory_logs` | 부품 입출고 이력 |

---

## 📊 더미데이터 내역

- **설비**: 50HP 스크류 콤프레샤 ×2, 30HP 스크류 콤프레샤, 20HP 피스톤 콤프레샤, 에어드라이어
- **운전로그**: 최근 30일치 (설비 4대 × 30일 = 120건)
- **에너지분석**: 최근 6개월치 데이터
- **시뮬레이션**: 인버터 교체, 운전 스케줄 최적화, 에어 누설 개선 등 3개 시나리오
- **정비이력**: 필터교체, 오일교체, 점검, 수리 등 6건
- **부품**: 필터, 오일, 벨트 등 8종

---

## 🔮 향후 확장 계획

- [ ] 바코드 스캔 기반 재고 관리 (구글폼 연동)
- [ ] 고객사별 멀티테넌트 구조
- [ ] 에너지 데이터 자동 수집 (IoT 센서 연동)
- [ ] PDF 보고서 자동 생성
- [ ] 모바일 최적화

---

*개발: KY Energy Management System v1.0.0 Demo*
