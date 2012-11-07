import veil_component

with veil_component.init_component(__name__):
    from .web_service import register_web_service
    from .web_service import WebFault

    __all__ = [
        register_web_service.__name__,
        WebFault.__name__
    ]

    def init():
        from veil.development.architecture import register_architecture_checker
        from .web_service import check_web_service_dependencies

        register_architecture_checker('WEB_SERVICES', check_web_service_dependencies)