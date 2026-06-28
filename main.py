import logging
from fastapi import FastAPI, Depends
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import declarative_base, sessionmaker, Session

# ----------------------------------------------------
# 0. 로그(Log) 일기장 설정 (블랙박스)
# ----------------------------------------------------
# 서버에서 일어나는 일을 'server.log'라는 파일에 시간순으로 자동 기록합니다.
logging.basicConfig(
    filename="server.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    encoding="utf-8"
)
logger = logging.getLogger("coupon_system")

# ----------------------------------------------------
# 1. DB 연결 및 테이블 설계
# ----------------------------------------------------
DB_URL = "mysql+pymysql://root:1234@localhost:3306/coupon_system"
engine = create_engine(DB_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class Coupon(Base):
    __tablename__ = "coupons"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), nullable=False)
    total_quantity = Column(Integer, nullable=False)
    remaining_quantity = Column(Integer, nullable=False)

class CouponIssue(Base):
    __tablename__ = "coupon_issues"
    id = Column(Integer, primary_key=True, index=True)
    coupon_id = Column(Integer, nullable=False)
    user_id = Column(Integer, nullable=False)

Base.metadata.create_all(bind=engine)

app = FastAPI(title="선착순 쿠폰 발급 서버")

# DB 창고 문을 열고 닫는 도우미 함수
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ----------------------------------------------------
# 2. API: 테스트용 쿠폰 100개 채워넣기
# ----------------------------------------------------
@app.post("/init")
def init_coupon(db: Session = Depends(get_db)):
    # 1. 기존 창고에 있던 발급 장부와 쿠폰들을 전부 불태워서(삭제) 깨끗하게 비웁니다.
    db.query(CouponIssue).delete()
    db.query(Coupon).delete()
    
    # 2. 강제로 '1번(id=1)' 이름표를 붙인 쿠폰 100개를 새로 창고에 넣습니다.
    new_coupon = Coupon(id=1, name="무적의 치킨 반값 쿠폰", total_quantity=100, remaining_quantity=100)
    db.add(new_coupon)
    db.commit()
    
    logger.info("DB 창고 완전 초기화 및 치킨 쿠폰 100개 재입고 완료.")
    return {"message": "초기화 완료! 치킨 쿠폰 100개 새로 장전되었습니다!"}

# ----------------------------------------------------
# 3. API: 유저가 쿠폰 발급받기
# ----------------------------------------------------
@app.post("/issue")
def issue_coupon(user_id: int, db: Session = Depends(get_db)):
    # 1번 쿠폰 정보 꺼내오기
    coupon = db.query(Coupon).filter(Coupon.id == 1).with_for_update().first()

    # 남은 수량이 0보다 크다면?
    if coupon.remaining_quantity > 0:
        coupon.remaining_quantity -= 1  # 1개 빼기
        
        # 누가 받았는지 장부에 기록
        new_issue = CouponIssue(coupon_id=1, user_id=user_id)
        db.add(new_issue)
        db.commit()

        # 정상 발급 로그 남기기
        logger.info(f"[성공] 유저 {user_id}번 쿠폰 발급 완료. (남은 수량: {coupon.remaining_quantity})")
        return {"message": f"유저 {user_id}님, 쿠폰 발급 성공! 남은 수량: {coupon.remaining_quantity}개"}
    
    # 0개라면? (매진)
    else:
        # 경고(Warning) 로그 남기기
        logger.warning(f"[실패] 유저 {user_id}번 발급 거절 - 쿠폰 매진됨.")
        return {"message": "죄송합니다. 선착순 쿠폰이 모두 매진되었습니다."}