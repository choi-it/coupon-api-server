# 선착순 쿠폰 발급 API 서버 (동시성 제어 프로젝트)

대규모 트래픽이 발생하는 '선착순 이벤트' 상황을 가정하여, 데이터의 무결성을 보장하고 초과 발급(Race Condition)을 방어하는 백엔드 API 서버입니다.

## Tech Stack
![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)
![MySQL](https://img.shields.io/badge/MySQL-4479A1?style=for-the-badge&logo=mysql&logoColor=white)

---

## 프로젝트 핵심 포인트

### 1. 동시성 제어 (Concurrency Control)
* **문제 상황:** 여러 명의 유저가 동시에 마지막 1개 남은 쿠폰 발급을 요청할 경우, DB 조회 시점의 지연으로 인해 재고가 마이너스(-)가 되거나 초과 발급되는 '경쟁 상태(Race Condition)'가 발생할 수 있습니다.
* **해결 방법:** SQLAlchemy의 `.with_for_update()`를 활용하여 데이터베이스 쿼리 레벨에서 **비관적 락(Pessimistic Lock)**을 구현했습니다.
* **적용 SQL 로직:**
* 특정 트랜잭션이 쿠폰 데이터를 조회하고 수정을 완료할 때까지 다른 요청의 접근을 대기시켜, 데이터의 정합성을 100% 보장하도록 방어했습니다.
  ```sql
  SELECT * FROM coupons WHERE id = 1 FOR UPDATE;
  ```
### 2. 에러 추적 및 상태 모니터링 (Logging)
* 서버 내부에서 발생하는 모든 이벤트를 추적하기 위해 server.log 파일에 시간순으로 로그를 기록하도록 구성했습니다.
* INFO 레벨: 정상적인 쿠폰 생성 및 발급 성공 내역 기록
* WARNING 레벨: 수량 소진(매진) 등 예외 상황 발생 시 기록하여, 시스템 에러와 비즈니스 로직 상의 거절을 명확히 구분했습니다.

<br>

**[로그 파일 기록 화면]**
![서버 로그 화면]
<img width="622" height="50" alt="logSC" src="https://github.com/user-attachments/assets/ad46374a-8e93-4462-8329-8b2d75ba7594" />


### 3. 데이터베이스 설계 (DB & RDBMS)
* coupons 테이블(재고 관리)과 coupon_issues 테이블(발급 내역)을 분리하여 정규화했습니다.
* SQLAlchemy ORM을 통해 파이썬 코드 내에서 객체 지향적으로 DB를 관리하며, 엔진 연결 시 Connection 설정을 통해 안정적으로 MySQL과 통신합니다.

<br>

**[MySQL Workbench 데이터베이스 테이블 화면]**
![MySQL Workbench 화면]
<img width="959" height="502" alt="Workbench" src="https://github.com/user-attachments/assets/04433299-8d57-4472-b34b-11011e71023e" />


### API 명세 (기능 요약)
* POST /init : 테스트용 쿠폰 100개를 DB에 초기화(생성)합니다.
* POST /issue?user_id={id} : 특정 유저에게 쿠폰을 발급하고 재고를 차감합니다. (Lock 적용 완료)

<br>

**[Swagger UI 테스트 화면]**
![Swagger UI 화면]
<img width="959" height="407" alt="log1" src="https://github.com/user-attachments/assets/0fa08d7a-fb74-408f-b144-a1390f9c9fce" />
<img width="959" height="410" alt="log2" src="https://github.com/user-attachments/assets/9f34f7fe-57e0-44e6-b3a1-83fa7ccfad76" />


### 실행 방법
* 로컬 환경에 MySQL 서버를 띄우고 coupon_system 데이터베이스를 생성합니다.
* pip install fastapi uvicorn sqlalchemy pymysql 모듈을 설치합니다.
* uvicorn main:app --reload 명령어로 서버를 실행합니다.
* http://127.0.0.1:8000/docs 에 접속하여 Swagger UI를 통해 API를 직접 테스트할 수 있습니다.

### 향후 개선 방향 (Next Steps)
* Redis 도입 고려: 현재는 RDBMS(MySQL)의 락(Lock)에 의존하고 있어 요청이 수만 건으로 몰릴 경우 DB 병목 현상이 우려됩니다. 향후 메모리 기반인 Redis를 도입하여 캐싱 처리 및 더 빠른 동시성 제어를 구현해 볼 계획입니다.
* 환경 변수 분리: 소스 코드 내에 하드코딩된 DB 접속 정보 등을 .env 파일로 분리하여 보안을 강화할 예정입니다.
