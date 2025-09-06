from datetime import datetime


def humanize_date(date_time: datetime | str) -> str:
    if date_time:
        diff = date_time.date() - datetime.now().date()
        days = diff.days

        if days == 0:
            return 'today'
        elif days == 1:
            return 'tomorrow'
        elif days == -1:
            return 'yesterday'
        else:
            if abs(days) <= 30:
                return_string = f'{abs(days)} days'
            else:
                months = round(days / 30)
                return_string = f'{abs(months)} month'

                if abs(months) > 1:
                    return_string = return_string + 's'

            if days > 0:
                return f'in {return_string}'
            else:
                return f'{return_string} ago'

    return ''
