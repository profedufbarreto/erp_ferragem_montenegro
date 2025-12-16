from app import create_app, db
from app.models.user import User

app = create_app()

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        
        # Verifica se o admin mestre já existe
        admin_exists = User.query.filter_by(username='admin').first()
        if not admin_exists:
            master_admin = User(
                username='admin', 
                password='123456789', 
                role='admin'
            )
            db.session.add(master_admin)
            db.session.commit()
            print(">>> Usuário Admin Mestre criado com sucesso!")

    app.run(debug=True)