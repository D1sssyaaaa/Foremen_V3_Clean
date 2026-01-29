"""Конфигурация pytest и фикстуры для тестов"""
import pytest
import sys
import os
from pathlib import Path

# Добавить backend в PYTHONPATH
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))
os.chdir(str(backend_dir))

# Импорты могут быть позже, когда путь настроен
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Попробуем импорт, если не получится - пропустим
try:
    from app.core.database import Base, get_db
    from app.core.models_base import UserRole
    from app.models import User, CostObject, Brigade, BrigadeMember
    HAS_APP = True
except ImportError:
    HAS_APP = False
    Base = None
    get_db = None


# База данных в памяти для тестов
SQLALCHEMY_TEST_DATABASE_URL = "sqlite:///:memory:"


@pytest.fixture(scope="function")
def db_session():
    """Создать тестовую БД и сессию"""
    if not HAS_APP or Base is None:
        pytest.skip("App not available")
    
    engine = create_engine(
        SQLALCHEMY_TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db_session):
    """Тестовый HTTP клиент FastAPI"""
    if not HAS_APP:
        pytest.skip("App not available")
    
    from fastapi.testclient import TestClient
    from app.main import app  # type: ignore
    
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as test_client:
        yield test_client
    
    app.dependency_overrides.clear()


@pytest.fixture
def test_user(db_session):
    """Создать тестового пользователя"""
    user = User(
        username="testuser",
        phone="+79001234567",
        role=[UserRole.MANAGER],
        hashed_password="$2b$12$fake_hashed_password"
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def test_foreman(db_session):
    """Создать тестового бригадира"""
    user = User(
        username="foreman1",
        phone="+79007654321",
        role=[UserRole.FOREMAN],
        hashed_password="$2b$12$fake_hashed_password"
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def test_object(db_session):
    """Создать тестовый объект"""
    from decimal import Decimal
    obj = CostObject(
        name="Тестовый объект",
        code="TEST-001",
        contract_number="Д-2024-001",
        contract_amount=Decimal("1000000.00")
    )
    db_session.add(obj)
    db_session.commit()
    db_session.refresh(obj)
    return obj


@pytest.fixture
def test_brigade(db_session, test_foreman):
    """Создать тестовую бригаду"""
    brigade = Brigade(
        name="Тестовая бригада №1",
        foreman_id=test_foreman.id
    )
    db_session.add(brigade)
    db_session.commit()
    db_session.refresh(brigade)
    
    # Добавить членов бригады
    members = [
        BrigadeMember(
            brigade_id=brigade.id,
            full_name="Иванов Иван Иванович",
            position="Маляр"
        ),
        BrigadeMember(
            brigade_id=brigade.id,
            full_name="Петров Петр Петрович",
            position="Штукатур"
        ),
        BrigadeMember(
            brigade_id=brigade.id,
            full_name="Сидоров Сидор Сидорович",
            position="Подсобник"
        )
    ]
    for member in members:
        db_session.add(member)
    db_session.commit()
    
    db_session.refresh(brigade)
    return brigade


@pytest.fixture
def auth_headers(test_user):
    """HTTP заголовки с токеном авторизации"""
    # В реальном приложении здесь генерировался бы JWT токен
    # Для тестов используем упрощенный вариант
    token = "test_token_" + str(test_user.id)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def sample_upd_xml():
    """Пример XML УПД для тестов"""
    return '''<?xml version="1.0" encoding="windows-1251"?>
<Файл xmlns="urn:СчФактура-5-01">
    <СвСчФакт НомерСчФ="123" ДатаСчФ="01.01.2024">
        <СвПрод>
            <ИдСв>
                <СвЮЛ НаимОрг="ООО Поставщик" ИННЮЛ="1234567890"/>
            </СвЮЛ>
        </СвПрод>
    </СвСчФакт>
    <ТаблСчФакт>
        <СведТов НомСтр="1" НаимТов="Цемент М500" КолТов="100" ОКЕИ_Тов="796" ЦенаТов="500" СтТовБезНДС="50000">
            <НалСт>20%</НалСт>
        </СведТов>
    </ТаблСчФакт>
</Файл>'''
