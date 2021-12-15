from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import Client, TestCase
from posts.models import Group, Post

User = get_user_model()


class PostsURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.group = Group.objects.create(
            title='Тестовый заголовок',
            description='Тестовое описание',
            slug='test-slug'
        )
        cls.post = Post.objects.create(
            text='Тестовый пост',
            author=User.objects.create_user(username='HasNoName'),
        )
        cls.difuser = User.objects.create_user(username='DifferentUser')

    def setUp(self):
        self.guest_client = Client()
        self.user = User.objects.get(username='HasNoName')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        cache.clear()

    def test_urls_exits_at_desired_location_for_guest_user(self):
        '''Страницы /, /group/test-slug/, /profile/HasNoName/, /posts/1/
        доступны любому пользователю,страницы /create/, /posts/1/edit/,
        /posts/1/comment, /profile/HasNoName/follow
        недоступны '''
        status_codes_url_names = {
            HTTPStatus.OK: ['/', f'/group/{self.group.slug}/',
                            f'/profile/{self.post.author.username}/',
                            f'/posts/{self.post.id}/'],
            HTTPStatus.FOUND: ['/create/', f'/posts/{self.post.id}/edit/',
                               f'/posts/{self.post.id}/comment/',
                               f'/profile/{self.post.author.username}/follow/',
                               f'/profile/{self.post.author.username}/'
                               'unfollow/'],
        }
        for status_code, list in status_codes_url_names.items():
            for adress in list:
                with self.subTest(adress=adress):
                    response = self.guest_client.get(adress)
                    self.assertEqual(response.status_code, status_code)

    def test_urls_exits_at_desired_location_for_authorized_user(self):
        '''Авторизированному пользователю доступы все страницы,
        страница /posts/5/edit/ доступна автору'''
        status_codes_url_names = {
            HTTPStatus.OK: ['/', f'/group/{self.group.slug}/',
                            f'/profile/{self.post.author.username}/',
                            f'/posts/{self.post.id}/',
                            '/create/', f'/posts/{self.post.id}/edit/']
        }
        for status_code, list in status_codes_url_names.items():
            for adress in list:
                with self.subTest(adress=adress):
                    response = self.authorized_client.get(adress)
                    self.assertEqual(response.status_code, status_code)

    def test_urls_redirect_correctly_for_guest_user(self):
        '''Неавторизированного пользователя перенаправляет на страницу входа'''
        redirect_urls_url_names = {
            '/auth/login/?next=/create/': '/create/',
            f'/auth/login/?next=/posts/{self.post.id}/edit/':
            f'/posts/{self.post.id}/edit/',
            f'/auth/login/?next=/posts/{self.post.id}/comment/':
            f'/posts/{self.post.id}/comment/',
            f'/auth/login/?next=/profile/{self.post.author.username}/follow/':
            f'/profile/{self.post.author.username}/follow/',
            f'/auth/login/?next=/profile/{self.post.author.username}/'
            'unfollow/': f'/profile/{self.post.author.username}/unfollow/'
        }
        for redirect_url, adress in redirect_urls_url_names.items():
            with self.subTest(adress=adress):
                response = self.guest_client.get(adress, follow=True)
                self.assertRedirects(response, redirect_url)

    def test_urls_redirect_correctly_edit_not_author(self):
        '''Возможность редактирования только для автора поста,
        другого пользователя перенаправит на страницу поста'''
        self.authorized_client.force_login(PostsURLTests.difuser)
        response = self.authorized_client.get(
            f'/posts/{self.post.id}/edit/', follow=True)
        self.assertRedirects(response, f'/posts/{self.post.id}/')

    def test_urls_uses_correct_template(self):
        '''Порверка используемых шаблонов'''
        urls_temlates_names = {
            '/': 'posts/index.html',
            f'/group/{self.group.slug}/': 'posts/group_list.html',
            f'/profile/{self.post.author.username}/': 'posts/profile.html',
            f'/posts/{self.post.id}/': 'post_detail.html',
            '/create/': 'posts/create_post.html',
            f'/posts/{self.post.id}/edit/': 'posts/create_post.html'
        }
        for adress, template in urls_temlates_names.items():
            with self.subTest(adress=adress):
                response = self.authorized_client.get(adress)
                self.assertTemplateUsed(response, template)
