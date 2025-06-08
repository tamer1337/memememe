from django import template

register = template.Library()

@register.filter
def correct_answers(answers):
    return answers.filter(is_correct=True)