import shutil
import tempfile

from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile

from posts.forms import PostForm, CommentForm
from posts.models import Post, Group, User, Comment

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class TaskCreateFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='test_user')
        cls.authorized_user = Client()
        cls.authorized_user.force_login(cls.user)
        cls.author = User.objects.create_user(username='author')
        cls.authorized_author = Client()
        cls.authorized_author.force_login(cls.author)
        cls.guest_user = Client()
        cls.group = Group.objects.create(title='test_title',
                                         slug='test_slug',
                                         description='test_description')
        cls.post = Post.objects.create(author=cls.author,
                                       id=33,
                                       text='test_text',
                                       group=cls.group,
                                       image='posts/small.png')
        cls.comment = Comment.objects.create(post=cls.post,
                                             author=cls.author,
                                             text='test_comment')
        cls.form = PostForm()
        cls.form_2 = CommentForm()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def test_create_post(self):
        """Валидная форма создает запись в Post."""
        posts_count = Post.objects.count()
        small_gif = (b'\x47\x49\x46\x38\x39\x61\x02\x00'
                     b'\x01\x00\x80\x00\x00\x00\x00\x00'
                     b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
                     b'\x00\x00\x00\x2C\x00\x00\x00\x00'
                     b'\x02\x00\x01\x00\x00\x02\x02\x0C'
                     b'\x0A\x00\x3B')
        uploaded = SimpleUploadedFile(
            name='small.png',
            content=small_gif,
            content_type='image/png'
        )
        form_data = {
            'text': 'test_text',
            'image': uploaded,
        }
        response = self.authorized_author.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertRedirects
        (response, reverse('posts:profile',
                           kwargs={'username': self.author.username}))
        self.assertEqual(Post.objects.count(), posts_count + 1)
        self.assertTrue(
            Post.objects.filter(
                text='test_text',
                id=33,
                image='posts/small.png'
            ).exists()
        )

    def test_post_edit_change_post(self):
        '''Проверяем что post_edit изменяет пост'''
        posts_count = Post.objects.count()
        form_data = {
            'text': 'test_text2',
        }
        response = self.authorized_author.post(
            reverse('posts:post_edit', kwargs={'post_id': 33}),
            data=form_data,
            follow=True)
        self.assertRedirects(response, reverse('posts:post_detail',
                                               kwargs={'post_id': 33}))
        self.assertEqual(Post.objects.count(), posts_count)
        one_more_responce = self.authorized_author.post(
            reverse('posts:post_detail', kwargs={'post_id': 33}))
        self.assertEqual
        (one_more_responce.context.get('page_obj').text, 'test_text2')

    def test_comment_form(self):
        '''comment_form добавляет новый коммент'''
        comments_count = Comment.objects.count()
        form_data = {
            'text': 'test_comment_2',
        }
        response = self.authorized_author.post(
            reverse('posts:add_comment', kwargs={'post_id': 33}),
            data=form_data,
            follow=True)
        self.assertRedirects(response, reverse('posts:post_detail',
                                               kwargs={'post_id': 33}))
        self.assertEqual(Comment.objects.count(), comments_count + 1)
