from get_media.model.user import User


def to_dict(user: User):
    return dict(
        username=user.username,
        fullname=user.fullname,
        birthday=user.birthday,
        phone=user.phone,
        email=user.email,
        instaLike=user.insta_like
    )
