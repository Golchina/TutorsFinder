from datetime import date

from .models import User, GENDERS


def get_user_data(user):
    """ Возвращает данные пользователя
        (id, почта, имя, фамилия, пол, дата рождения, возраст, город, ссылка на изображения профиля)
    """
    data = {
        "id": user.id,
        "email": user.email,
        "name": user.name,
        "surname": user.surname,
        "gender": user.get_gender_display,
        "birthday": user.birthday,
        "age": get_current_age(user.birthday) if user.birthday else None,
        "city": user.city,
        "profile_image_url": user.profile_image.url if user.profile_image else None
    }
    return data


def get_current_age(birthday):
    """ Подсчитывает и возвращает текущий возраст из даты рождения """
    today = date.today()
    # формула: текущий год - год рождения - (True=>1, если день рождения еще не наступил или False=>0, если наступил)
    return today.year - birthday.year - ((today.month, today.day) < (birthday.month, birthday.day))
