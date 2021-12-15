from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase
from django.urls import reverse
from posts.forms import PostForm
from posts.models import Comment, Group, Post

User = get_user_model()


class PostsFormsTests(TestCase):
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
        cls.form = PostForm()

    def setUp(self):
        self.user = User.objects.get(username=PostsFormsTests.author.username)
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_create_post(self):
        '''При создании поста появляется запись в бд'''
        post_count = Post.objects.count()
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
        form_data = {
            'text': 'NewPost',
            'group': PostsFormsTests.group.id,
            'image': uploaded
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertRedirects(response,
                             reverse('posts:profile',
                                     kwargs={'username':
                                             PostsFormsTests.author.username}))
        self.assertEqual(Post.objects.count(), post_count + 1)
        self.assertTrue(
            Post.objects.filter(
                text=form_data['text'],
                group=PostsFormsTests.group
            ).exists()
        )

    def test_post_edit(self):
        post_count = Post.objects.count()
        form_data = {
            'text': 'NewPost'
        }
        response = self.authorized_client.post(
            reverse('posts:post_edit', args=f'{PostsFormsTests.post.id}'),
            data=form_data,
            follow=True
        )
        self.assertRedirects(response,
                             reverse('posts:post_detail',
                                     kwargs={'post_id':
                                             PostsFormsTests.post.id}))
        self.assertEqual(Post.objects.count(), post_count)
        self.assertTrue(
            Post.objects.filter(
                text=form_data['text'],
            ).exists()
        )

    def test_comment(self):
        form_data = {
            'text': 'NewComment'
        }
        comment_count = Comment.objects.count()
        response = self.authorized_client.post(
            reverse('posts:add_comment', args=f'{PostsFormsTests.post.id}'),
            data=form_data,
            follow=True
        )
        self.assertEqual(Comment.objects.count(), comment_count + 1)
        self.assertContains(response, 'NewComment')
