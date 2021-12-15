from django import forms
from posts.models import Comment, Post


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ('text', 'group', 'image')
        labels = {
            'text': 'Тут будет пост',
            'group': 'А вот тут - группа',
        }
        help_texts = {
            'text': 'Вот прям сюда пиши!',
            'group': 'Группа, к которой будет относиться пост',
        }


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ('text',)
        help_texts = {
            'text': 'Сюда комментарий пиши'
        }
