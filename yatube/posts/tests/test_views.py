from django import forms
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase
from django.urls import reverse
from posts.models import Follow, Group, Post

User = get_user_model()


class PostsVIEWTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.group = Group.objects.create(
            title='Тестовый заголовок',
            description='Тестовое описание',
            slug='test-slug'
        )
        cls.author = User.objects.create_user(username='HasNoName')
        cls.post = Post.objects.create(
            text='Пост',
            author=cls.author,
            group=cls.group,
        )
        cls.group2 = Group.objects.create(
            title='Тестовый заголовок 2',
            description='Тестовое описание 2',
            slug='test-slug2'
        )
        cls.author2 = User.objects.create_user(username='DifName')
        cls.form_fields = {
            'group': forms.fields.ChoiceField,
            'text': forms.fields.CharField,
        }

    def setUp(self):
        self.post2 = Post.objects.create(
            text='Лишний пост',
            author=self.author2,
            group=self.group2,
        )
        self.user = User.objects.get(username=PostsVIEWTests.author.username)
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        cache.clear()

    def compare_posts_fields(self, post: Post, post2: Post):
        self.assertEqual(post.text, post2.text)
        self.assertEqual(post.group, post2.group)
        self.assertEqual(post.author, post2.author)
        self.assertEqual(post.image, post2.image)

    def test_names_and_namespaces(self):
        '''Порверка используемых namespace:name'''
        reverse_names_temlates_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse('posts:group_posts',
                    kwargs={'slug': PostsVIEWTests.group.slug}): 'posts/group'
                                                                 '_list.html',
            reverse('posts:profile',
                    kwargs={'username': PostsVIEWTests.author.username}
                    ): 'posts/profile.html',
            reverse('posts:post_detail',
                    kwargs={'post_id':
                            PostsVIEWTests.post.id}): 'post_detail.html',
            reverse('posts:post_create'): 'posts/create_post.html',
            reverse('posts:post_edit',
                    kwargs={'post_id':
                            PostsVIEWTests.post.id}): ('posts/'
                                                       'create_post.html')
        }
        for reverse_name, template in reverse_names_temlates_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_index_view_show_correct_context(self):
        '''На главную страницу корректно выводятся все посты,
        работает кэширование'''
        response = self.authorized_client.get(reverse('posts:index'))
        post = response.context['page_obj'][0]
        self.compare_posts_fields(post, self.post2)
        Post.objects.filter(id=self.post2.id).delete()
        response = self.authorized_client.get(reverse('posts:index'))
        self.assertContains(response, 'Лишний пост')
        cache.clear()
        response = self.authorized_client.get(reverse('posts:index'))
        self.assertNotContains(response, 'Лишний пост')

    def test_groups_view_show_correct_context(self):
        '''На странице группы только посты группы, посты пердаются корректно'''
        response = self.authorized_client.get(
            reverse('posts:group_posts',
                    kwargs={'slug': PostsVIEWTests.group.slug}))
        posts = response.context['page_obj']
        self.compare_posts_fields(posts[0], self.post)
        for post in posts:
            self.assertEqual(post.group, PostsVIEWTests.post.group)

    def test_profile_view_show_correct_context(self):
        '''На странице профиля только посты автора,
        посты пердаются корректно'''
        response = self.authorized_client.get(
            reverse('posts:profile',
                    kwargs={'username': PostsVIEWTests.author.username}))
        posts = response.context['page_obj']
        self.compare_posts_fields(posts[0], self.post)
        for post in posts:
            self.assertEqual(post.author, PostsVIEWTests.post.author)

    def test_post_detail_view_show_correct_context(self):
        '''В информации о посте корректные данные'''
        response = self.authorized_client.get(
            reverse('posts:post_detail',
                    kwargs={'post_id': PostsVIEWTests.post.id}))
        post = response.context['post']
        self.compare_posts_fields(post, self.post)

    def test_post_edit_show_correct_context(self):
        '''Передаётся форма с необходимимы полями'''
        response = self.authorized_client.get(
            reverse('posts:post_edit',
                    kwargs={'post_id': PostsVIEWTests.post.id}))
        objects = response.context['post']
        self.assertEqual(objects, PostsVIEWTests.post)
        for value, expected in PostsVIEWTests.form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_post_create_correct_context(self):
        '''Передаётся форма с необходимимы полями'''
        response = self.authorized_client.get(reverse('posts:post_create'))
        for value, expected in PostsVIEWTests.form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_new_post_exist(self):
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        new_post = Post.objects.create(
            text='NewPost',
            author=PostsVIEWTests.author,
            group=PostsVIEWTests.group,
            image=uploaded
        )
        response = self.authorized_client.get(reverse('posts:index'))
        post = response.context['page_obj'][0]
        self.assertEqual(new_post, post)
        response = self.authorized_client.get(
            reverse('posts:profile',
                    kwargs={'username': PostsVIEWTests.author.username}))
        posts = response.context['page_obj']
        self.assertIn(new_post, posts)
        response = self.authorized_client.get(
            reverse('posts:group_posts',
                    kwargs={'slug': PostsVIEWTests.group.slug}))
        posts = response.context['page_obj']
        self.assertIn(new_post, posts)
        response = self.authorized_client.get(
            reverse('posts:group_posts',
                    kwargs={'slug': PostsVIEWTests.group2.slug}))
        posts = response.context['page_obj']
        self.assertNotIn(new_post, posts)

    def test_follow(self):
        '''Авторизованный пользователь может подписываться на других
        пользователей,
        новая запись пользователя появляется в ленте тех,
        кто на него подписан и не появляется в ленте тех, кто не подписан'''
        self.authorized_client.get(
            reverse('posts:profile_follow',
                    kwargs={'username': PostsVIEWTests.author2.username}))
        self.assertTrue(Follow.objects.filter(
            author=PostsVIEWTests.author2).filter(user=self.author).exists())
        Post.objects.create(
            text='TestFollowIndex',
            author=PostsVIEWTests.author2
        )
        response = self.authorized_client.get(reverse('posts:follow_index'))
        self.assertContains(response, 'TestFollowIndex')
        new_user = Client()
        new_user.force_login(User.objects.create_user(username='TestUser'))
        response = new_user.get(reverse('posts:follow_index'))
        self.assertNotContains(response, 'TestFollowIndex')
        self.authorized_client.get(
            reverse('posts:profile_unfollow',
                    kwargs={'username': PostsVIEWTests.author2.username}))
        self.assertFalse(Follow.objects.filter(
            author=PostsVIEWTests.author2).filter(user=self.author).exists())

    def test_unfollow(self):
        '''Проверка отписки'''
        self.authorized_client.get(
            reverse('posts:profile_follow',
                    kwargs={'username': PostsVIEWTests.author2.username}))
        self.authorized_client.get(
            reverse('posts:profile_unfollow',
                    kwargs={'username': PostsVIEWTests.author2.username}))
        self.assertFalse(Follow.objects.filter(
            author=PostsVIEWTests.author2).filter(user=self.author).exists())


class PaginatorTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.group = Group.objects.create(
            title='Тестовый заголовок',
            description='Тестовое описание',
            slug='test-slug'
        )
        cls.group2 = Group.objects.create(
            title='Тестовый заголовок 2',
            description='Тестовое описание 2',
            slug='test-slug2'
        )
        cls.author = User.objects.create_user(username='HasNoName')
        cls.author2 = User.objects.create_user(username='DifName')
        cls.post = Post.objects.create(
            text='Лишний пост',
            author=cls.author2,
            group=cls.group2,
            id=0,
        )
        for counter in range(0, 15):
            Post.objects.create(
                text=f'Пост № {counter}',
                author=cls.author,
                group=cls.group,
            )
        cls.form_fields = {
            'group': forms.fields.ChoiceField,
            'text': forms.fields.CharField,
        }

    def setUp(self):
        self.user = User.objects.get(username=PaginatorTests.author.username)
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        cache.clear()

    def test_paginator(self):
        reverse_int = {
            reverse('posts:index'): 6,
            reverse('posts:group_posts',
                    kwargs={'slug': PaginatorTests.group.slug}): 5,
            reverse('posts:profile',
                    kwargs={'username': PaginatorTests.author.username}): 5,
        }
        for reverse_name, intgr in reverse_int.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertEqual(len(response.context['page_obj']), 10)
                response = self.authorized_client.get(reverse_name + '?page=2')
                self.assertEqual(len(response.context['page_obj']), intgr)
