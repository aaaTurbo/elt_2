class DomainError(Exception):
    """Бизнес-ошибка, ожидаемая и обрабатываемая на уровне API."""


class NotFoundError(DomainError):
    pass


class ConflictError(DomainError):
    pass


class ValidationError(DomainError):
    pass


class KeitaroError(DomainError):
    pass
