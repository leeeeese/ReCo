"""
CSV 파일을 데이터베이스로 마이그레이션하는 스크립트
중고나라 상품 데이터를 DB에 업로드
"""

import pandas as pd
import sys
from pathlib import Path
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from tqdm import tqdm
from server.db.database import SessionLocal, engine
from server.db.models import Product, Seller, Review, Base


def create_tables():
    """테이블 생성"""
    Base.metadata.create_all(bind=engine)
    print("테이블 생성 완료")


def clean_seller_code(code):
    """seller_code에서 BOM 문자 제거"""
    if isinstance(code, str):
        return code.strip().replace('\ufeff', '')
    return code


def migrate_item_details(csv_path: str, clear_existing: bool = False):
    """
    item_detail_data.csv를 DB로 마이그레이션

    Args:
        csv_path: CSV 파일 경로
        clear_existing: 기존 데이터 삭제 여부
    """
    print(f"\nitem_detail_data.csv 파일 읽기 중...")

    # CSV 파일 읽기
    try:
        df = pd.read_csv(csv_path, encoding='utf-8')
    except UnicodeDecodeError:
        try:
            df = pd.read_csv(csv_path, encoding='cp949')
        except:
            df = pd.read_csv(csv_path, encoding='euc-kr')

    print(f"총 {len(df)}개 행 읽기 완료")

    # seller_code 정리
    df['seller_code'] = df['seller_code'].apply(clean_seller_code)

    # DB 연결
    db: Session = SessionLocal()

    try:
        # 기존 데이터 삭제 (선택사항)
        if clear_existing:
            print("기존 상품 데이터 삭제 중...")
            db.query(Product).delete()
            db.commit()
            print("기존 데이터 삭제 완료")

        # 상품 데이터 삽입
        print("상품 데이터 삽입 중...")
        batch_size = 1000
        total_batches = (len(df) + batch_size - 1) // batch_size

        for i in tqdm(range(0, len(df), batch_size), desc="상품 삽입 진행"):
            batch = df[i:i + batch_size]

            for _, row in batch.iterrows():
                try:
                    product_id = int(row['item_code']) if pd.notna(
                        row['item_code']) else None
                    seller_id = int(row['seller_code']) if pd.notna(
                        row['seller_code']) else None

                    if not product_id or not seller_id:
                        continue

                    # 기존 상품 확인
                    existing_product = db.query(Product).filter(
                        Product.product_id == product_id).first()

                    product_data = {
                        'product_id': product_id,
                        'seller_id': seller_id,
                        'title': str(row['item_name']) if pd.notna(row['item_name']) else '',
                        'price': float(row['item_price']) if pd.notna(row['item_price']) else 0.0,
                        'category': str(row['category_mid']) if pd.notna(row['category_mid']) else '',
                        'category_top': str(row['category_top']) if pd.notna(row['category_top']) else '',
                        'condition': str(row['item_status']) if pd.notna(row['item_status']) else '',
                        'description': str(row['item_caption']) if pd.notna(row['item_caption']) else '',
                        'view_count': int(row['item_view']) if pd.notna(row['item_view']) else 0,
                        'like_count': int(row['item_like']) if pd.notna(row['item_like']) else 0,
                        'chat_count': int(row['item_chat']) if pd.notna(row['item_chat']) else 0,
                        'sell_method': str(row['sell_method']) if pd.notna(row['sell_method']) else '',
                        'delivery_fee': str(row['delivery_fee']) if pd.notna(row['delivery_fee']) else '',
                        'is_safe': str(row['is_safe']) if pd.notna(row['is_safe']) else '',
                    }

                    if existing_product:
                        # 업데이트
                        for key, value in product_data.items():
                            if key != 'product_id':
                                setattr(existing_product, key, value)
                    else:
                        # 신규 삽입
                        product = Product(**product_data)
                        db.add(product)

                except Exception as e:
                    print(f"상품 {row.get('item_code', 'unknown')} 처리 오류: {e}")
                    continue

            db.commit()

        # 통계 출력
        total_products = db.query(Product).count()
        print(f"\n상품 데이터 마이그레이션 완료: {total_products}개")

    except Exception as e:
        db.rollback()
        print(f"오류 발생: {e}")
        raise
    finally:
        db.close()


def migrate_sellers(csv_path: str, clear_existing: bool = False):
    """
    seller_data.csv를 DB로 마이그레이션

    Args:
        csv_path: CSV 파일 경로
        clear_existing: 기존 데이터 삭제 여부
    """
    print(f"\nseller_data.csv 파일 읽기 중...")

    # CSV 파일 읽기
    try:
        df = pd.read_csv(csv_path, encoding='utf-8')
    except UnicodeDecodeError:
        try:
            df = pd.read_csv(csv_path, encoding='cp949')
        except:
            df = pd.read_csv(csv_path, encoding='euc-kr')

    print(f"총 {len(df)}개 행 읽기 완료")

    # seller_code 정리 (BOM 제거)
    df.columns = [col.replace('\ufeff', '') for col in df.columns]
    if 'seller_code' in df.columns:
        df['seller_code'] = df['seller_code'].apply(clean_seller_code)

    # DB 연결
    db: Session = SessionLocal()

    try:
        # 기존 데이터 삭제 (선택사항)
        if clear_existing:
            print("기존 판매자 데이터 삭제 중...")
            db.query(Seller).delete()
            db.commit()
            print("기존 데이터 삭제 완료")

        # 판매자 데이터 삽입
        print("판매자 데이터 삽입 중...")

        for _, row in tqdm(df.iterrows(), total=len(df), desc="판매자 삽입 진행"):
            try:
                seller_id = int(row['seller_code']) if pd.notna(
                    row['seller_code']) else None

                if not seller_id:
                    continue

                # 기존 판매자 확인
                existing_seller = db.query(Seller).filter(
                    Seller.seller_id == seller_id).first()

                seller_data = {
                    'seller_id': seller_id,
                    'seller_name': str(row['seller_name']) if pd.notna(row['seller_name']) else f'판매자{seller_id}',
                    'seller_trust': float(row['seller_trust']) if pd.notna(row['seller_trust']) else 0.0,
                    'seller_safe_sales': int(row['seller_safe_sales']) if pd.notna(row['seller_safe_sales']) else 0,
                    'seller_customs': int(row['seller_customs']) if pd.notna(row['seller_customs']) else 0,
                    'seller_items': int(row['seller_items']) if pd.notna(row['seller_items']) else 0,
                    'category_top': str(row['category_top']) if pd.notna(row['category_top']) else '',
                    'sell_method': str(row['sell_method']) if pd.notna(row['sell_method']) else '',
                    'seller_view': int(row['seller_view']) if pd.notna(row['seller_view']) else 0,
                    'seller_like': int(row['seller_like']) if pd.notna(row['seller_like']) else 0,
                    'seller_chat': int(row['seller_chat']) if pd.notna(row['seller_chat']) else 0,
                }

                if existing_seller:
                    # 업데이트
                    for key, value in seller_data.items():
                        if key != 'seller_id':
                            setattr(existing_seller, key, value)
                else:
                    # 신규 삽입
                    seller = Seller(**seller_data)
                    db.add(seller)

            except Exception as e:
                print(f"판매자 {row.get('seller_code', 'unknown')} 처리 오류: {e}")
                continue

        db.commit()

        # 통계 출력
        total_sellers = db.query(Seller).count()
        print(f"\n판매자 데이터 마이그레이션 완료: {total_sellers}개")

    except Exception as e:
        db.rollback()
        print(f"오류 발생: {e}")
        raise
    finally:
        db.close()


def migrate_reviews(csv_path: str, clear_existing: bool = False):
    """
    review_data.csv를 DB로 마이그레이션

    Args:
        csv_path: CSV 파일 경로
        clear_existing: 기존 데이터 삭제 여부
    """
    print(f"\nreview_data.csv 파일 읽기 중...")

    # CSV 파일 읽기
    try:
        df = pd.read_csv(csv_path, encoding='utf-8')
    except UnicodeDecodeError:
        try:
            df = pd.read_csv(csv_path, encoding='cp949')
        except:
            df = pd.read_csv(csv_path, encoding='euc-kr')

    print(f"총 {len(df)}개 행 읽기 완료")

    # seller_code 정리 (BOM 제거)
    df.columns = [col.replace('\ufeff', '') for col in df.columns]
    if 'seller_code' in df.columns:
        df['seller_code'] = df['seller_code'].apply(clean_seller_code)

    # DB 연결
    db: Session = SessionLocal()

    try:
        # 기존 데이터 삭제 (선택사항)
        if clear_existing:
            print("기존 리뷰 데이터 삭제 중...")
            db.query(Review).delete()
            db.commit()
            print("기존 데이터 삭제 완료")

        # 리뷰 데이터 삽입
        print("리뷰 데이터 삽입 중...")

        for _, row in tqdm(df.iterrows(), total=len(df), desc="리뷰 삽입 진행"):
            try:
                seller_id = int(row['seller_code']) if pd.notna(
                    row['seller_code']) else None

                if not seller_id:
                    continue

                review_data = {
                    'reviewer_id': str(row['reviewer_id']) if pd.notna(row['reviewer_id']) else '',
                    'review_role': str(row['review_role']) if pd.notna(row['review_role']) else '',
                    'review_content': str(row['review_content']) if pd.notna(row['review_content']) else '',
                    'seller_id': seller_id,
                    'seller_name': str(row['seller_name']) if pd.notna(row['seller_name']) else '',
                }

                # 신규 삽입 (리뷰는 중복 가능하므로 항상 추가)
                review = Review(**review_data)
                db.add(review)

            except Exception as e:
                print(f"리뷰 처리 오류: {e}")
                continue

        db.commit()

        # 통계 출력
        total_reviews = db.query(Review).count()
        print(f"\n리뷰 데이터 마이그레이션 완료: {total_reviews}개")

    except Exception as e:
        db.rollback()
        print(f"오류 발생: {e}")
        raise
    finally:
        db.close()


def migrate_all(csv_dir: str = ".", clear_existing: bool = False):
    """
    모든 CSV 파일을 DB로 마이그레이션

    Args:
        csv_dir: CSV 파일이 있는 디렉토리
        clear_existing: 기존 데이터 삭제 여부 (테이블도 재생성)
    """
    csv_dir_path = Path(csv_dir)

    item_csv = csv_dir_path / "item_detail_data.csv"
    seller_csv = csv_dir_path / "seller_data.csv"
    review_csv = csv_dir_path / "review_data.csv"

    # clear_existing이면 기존 테이블 삭제
    if clear_existing:
        Base.metadata.drop_all(bind=engine)

    # 테이블 생성
    create_tables()

    # 판매자 먼저 마이그레이션 (상품이 판매자 참조)
    if seller_csv.exists():
        migrate_sellers(str(seller_csv), clear_existing=clear_existing)
    else:
        print(f"경고: {seller_csv} 파일을 찾을 수 없습니다.")

    # 상품 마이그레이션
    if item_csv.exists():
        migrate_item_details(str(item_csv), clear_existing=clear_existing)
    else:
        print(f"경고: {item_csv} 파일을 찾을 수 없습니다.")

    # 리뷰 마이그레이션 (판매자 이후)
    if review_csv.exists():
        migrate_reviews(str(review_csv), clear_existing=clear_existing)
    else:
        print(f"경고: {review_csv} 파일을 찾을 수 없습니다.")

    print("\n모든 마이그레이션 완료!")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("사용법: python -m server.db.migrate_csv <csv_directory> [--clear]")
        print("예시: python -m server.db.migrate_csv . --clear")
        print("      python -m server.db.migrate_csv /path/to/csv/files")
        sys.exit(1)

    csv_dir = sys.argv[1]
    clear_existing = "--clear" in sys.argv

    # 마이그레이션 실행
    migrate_all(csv_dir, clear_existing=clear_existing)
