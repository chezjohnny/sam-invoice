from . import database
from .customer import Customer


def create_customer(name: str, address: str, email: str):
    session = database.SessionLocal()
    customer = Customer(name=name, address=address, email=email)
    session.add(customer)
    session.commit()
    session.refresh(customer)
    session.close()
    return customer


def get_customers():
    session = database.SessionLocal()
    customers = session.query(Customer).all()
    session.close()
    return customers


def get_customer_by_id(customer_id: int):
    session = database.SessionLocal()
    customer = session.query(Customer).filter(Customer.id == customer_id).first()
    session.close()
    return customer


def update_customer(customer_id: int, name: str = None, address: str = None, email: str = None):
    session = database.SessionLocal()
    customer = session.query(Customer).filter(Customer.id == customer_id).first()
    if customer:
        if name:
            customer.name = name
        if address:
            customer.address = address
        if email:
            customer.email = email
        session.commit()
        session.refresh(customer)
    session.close()
    return customer


def delete_customer(customer_id: int):
    session = database.SessionLocal()
    customer = session.query(Customer).filter(Customer.id == customer_id).first()
    if customer:
        session.delete(customer)
        session.commit()
    session.close()
    return customer
