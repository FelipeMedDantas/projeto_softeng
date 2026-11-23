import reflex as rx

config = rx.Config(
    app_name="app",
    frontend_port=3000,
    backend_port=8000,
    backend_host="0.0.0.0",
    api_url="http://localhost:8000",
    show_built_with_reflex=False,
    plugins=[
        rx.plugins.SitemapPlugin(),
        rx.plugins.TailwindV4Plugin(),
        rx.plugins.RadixThemesPlugin(),
    ]
)