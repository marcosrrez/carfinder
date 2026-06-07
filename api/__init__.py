# api/__init__.py
def register_blueprints(app):
    from api.searches import searches_bp
    from api.listings import listings_bp
    from api.scan import scan_bp
    from api.push import push_bp
    app.register_blueprint(searches_bp)
    app.register_blueprint(listings_bp)
    app.register_blueprint(scan_bp)
    app.register_blueprint(push_bp)
