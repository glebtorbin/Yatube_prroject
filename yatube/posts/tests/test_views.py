from django.core.cache import cache
import shutil
import tempfile

from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import TestCase, Client, override_settings
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile

from posts.models import Post, Group, Comment, Follow

User = get_user_model()

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostsViewsTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='test_user')
        cls.author = User.objects.create_user(username='author')
        cls.guest_user = Client()
        cls.group = Group.objects.create(title='test_title',
                                         slug='test_slug',
                                         description='test_description')
        cls.small_gif = (b'\x47\x49\x46\x38\x39\x61\x02\x00'
                         b'\x01\x00\x80\x00\x00\x00\x00\x00'
                         b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
                         b'\x00\x00\x00\x2C\x00\x00\x00\x00'
                         b'\x02\x00\x01\x00\x00\x02\x02\x0C'
                         b'\x0A\x00\x3B')
        cls.uploaded = SimpleUploadedFile(name='test.png',
                                          content=cls.small_gif,
                                          content_type='image/png')
        cls.post = Post.objects.create(author=cls.author,
                                       id=33,
                                       text='test_text',
                                       group=cls.group,
                                       image=cls.uploaded)
        for i in range(0, 13):
            cls.post_2 = Post.objects.create(author=cls.author,
                                             text='test_text',
                                             group=cls.group,
                                             image=cls.post.image)
        cls.templates_pages_names = {
            reverse('posts:index'):
            'posts/index.html',
            reverse('posts:group_list', kwargs={'slug': 'test_slug'}):
            'posts/group_list.html',
            reverse('posts:profile', kwargs={'username': 'author'}):
            'posts/profile.html',
            reverse('posts:post_detail', kwargs={'post_id': '33'}):
            'posts/post_detail.html',
            reverse('posts:post_create'):
            'posts/create_post.html',
            reverse('posts:post_edit', kwargs={'post_id': '33'}):
            'posts/create_post.html',

        }

    def setUp(self):
        self.authorized_author = Client()
        self.authorized_author.force_login(self.author)
        self.authorized_user = Client()
        self.authorized_user.force_login(self.user)
        cache.clear()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        for reverse_name, template in self.templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_author.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_index_page_show_correct_context(self):
        """Шаблон index сформирован с правильным контекстом."""
        response = self.authorized_author.get(reverse('posts:index'))
        first_object = response.context['page_obj'][0]
        task_text_0 = first_object.text
        task_image_0 = Post.objects.first().image
        self.assertEqual(task_text_0, 'test_text')
        self.assertEqual(task_image_0, 'posts/test.png')

    def test_group_list_page_show_correct_context(self):
        """Шаблон group_list сформирован с правильным контекстом."""
        response = (self.authorized_author.
                    get(reverse('posts:group_list',
                                kwargs={'slug': 'test_slug'})))
        first_object = response.context['page_obj'][0]
        post_image_0 = first_object.image
        self.assertEqual(post_image_0, 'posts/test.png')
        self.assertEqual(response.context.get('group').title, 'test_title')
        self.assertEqual(response.context.get('group').slug, 'test_slug')

    def test_profile_page_show_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом."""
        response = self.authorized_author.get(reverse('posts:profile',
                                              kwargs={'username': 'author'}))
        first_object = response.context['page_obj'][0]
        post_text_0 = first_object.text
        post_author_0 = first_object.author.username
        post_group_0 = first_object.group.title
        post_date_0 = first_object.pub_date.strftime("%Y-%m-%d")
        post_image_0 = Post.objects.first().image
        self.assertEqual(post_text_0, 'test_text')
        self.assertEqual(post_author_0, 'author')
        self.assertEqual(post_group_0, 'test_title')
        self.assertEqual(post_date_0, self.post.pub_date.strftime("%Y-%m-%d"))
        self.assertEqual(post_image_0, 'posts/test.png')

    def test_post_detail_page_show_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        response = self.authorized_author.get(reverse('posts:post_detail',
                                              kwargs={'post_id': '33'}))
        self.assertEqual(response.context.get('page_obj').text, 'test_text')
        self.assertEqual(response.context.get('page_obj').image,
                         'posts/test.png')

    def test_post_edit_page_show_correct_context(self):
        """Шаблон post_edit сформирован с правильным контекстом."""
        response = self.authorized_author.get(reverse('posts:post_edit',
                                              kwargs={'post_id': '33'}))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_post_create_page_show_correct_context(self):
        """Шаблон post_create сформирован с правильным контекстом."""
        response = self.authorized_author.get(reverse('posts:post_create'))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_pagination_pages_index_group_list_profile(self):
        '''Проверка пагинации страниц index, group_list, profile'''
        pages = {
            reverse('posts:index'): 10,
            reverse('posts:group_list', kwargs={'slug': 'test_slug'}): 10,
            reverse('posts:profile', kwargs={'username': 'author'}): 10,
        }
        for address, expected_pages in pages.items():
            with self.subTest(address=address):
                response = self.guest_user.get(address)
                self.assertEqual
                (len(response.context['page_obj']), expected_pages)


class PostsViewsTestsIndex(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.group = Group.objects.create(title='test_title1',
                                         slug='test-slug1',
                                         description='test-description')
        cls.author = User.objects.create_user(username='author')
        cls.post = Post.objects.create(author=cls.author,
                                       id=15,
                                       text='test_test',
                                       group=cls.group)
        cls.comment = Comment.objects.create(post=cls.post,
                                             author=cls.author,
                                             text='test_comment')

    def setUp(self):
        self.authorized_author = Client()
        self.authorized_author.force_login(self.author)

    def test_index_page_show_post(self):
        '''если при создании поста указать группу, то этот пост появляется
           на главной странице сайта'''
        response = self.authorized_author.get(reverse('posts:index'))
        first_object = response.context['page_obj'][0]
        task_text_0 = first_object.group.title
        self.assertEqual(task_text_0, 'test_title1')

    def test_group_list_last_obj(self):
        '''если при создании поста указать группу, то этот пост появляется
           на странице группы'''
        response = self.authorized_author.get(reverse('posts:group_list',
                                              kwargs={'slug': 'test-slug1'}))
        first_object = response.context['page_obj'][0]
        task_text_0 = first_object.text
        task_id_0 = first_object.id
        self.assertEqual(task_text_0, 'test_test')
        self.assertEqual(task_id_0, 15)

    def test_profile_last_obj(self):
        '''если при создании поста указать группу, то этот пост появляется
           на странице профайла пользователя'''
        response = self.authorized_author.get(reverse('posts:profile',
                                              kwargs={'username': 'author'}))
        first_object = response.context['page_obj'][0]
        task_text_0 = first_object.group.title
        self.assertEqual(task_text_0, 'test_title1')


class CacheTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.post = Post.objects.create(
            author=User.objects.create_user(username='test_name',
                                            email='test@mail.ru',
                                            password='test_password',),
            text='test_text')

    def setUp(self):
        self.guest_client = Client()
        self.user = User.objects.create_user(username='test_username')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_cache_index(self):
        """Тест кэширования страницы posts:index"""
        first_get = self.authorized_client.get(reverse('posts:index'))
        post_1 = Post.objects.get(id=1)
        post_1.text = 'test_text_2'
        post_1.save()
        second_get = self.authorized_client.get(reverse('posts:index'))
        self.assertEqual(first_get.content, second_get.content)
        cache.clear()
        third_get = self.authorized_client.get(reverse('posts:index'))
        self.assertNotEqual(first_get.content, third_get.content)


class FollowTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create(username='test_name',
                                         email='test@mail.ru',
                                         password='test_password',)
        cls.post = Post.objects.create(author=cls.author,
                                       text='test_text',
                                       id=228)

    def setUp(self):
        self.guest_client = Client()
        self.user = User.objects.create_user(username='test_username')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_followed_author_posts_in_profile_follow(self):
        '''Проверяем что запись появляется у подписчика в pofile_follow'''
        self.authorized_client.get(reverse('posts:profile_follow',
                                   kwargs={'username': self.author.username}))
        response = self.authorized_client.get(reverse('posts:follow_index'))
        first_object = response.context['page_obj'][0]
        task_text_0 = first_object.text
        task_id_0 = first_object.id
        self.assertEqual(task_text_0, 'test_text')
        self.assertEqual(task_id_0, 228)

    def test_user_can_follow(self):
        '''Проверяем что авторизованный пользователь может
           подписываться на авторов'''
        follow_count = Follow.objects.all().count()
        self.authorized_client.get(reverse('posts:profile_follow',
                                           kwargs={'username':
                                                   self.author.
                                                   username}))
        one_more_follow_count = Follow.objects.count()
        self.assertEqual(follow_count + 1, one_more_follow_count)

    def test_user_can_unfollow(self):
        '''Проверяем что авторизованный пользователь
           может отписываться от авторов'''
        follow_count = Follow.objects.count()
        self.authorized_client.get(reverse('posts:profile_follow',
                                           kwargs={'username':
                                                   self.author.
                                                   username}))
        self.authorized_client.get(reverse('posts:profile_unfollow',
                                           kwargs={'username':
                                                   self.author.username}))
        one_more_follow_count = Follow.objects.count()
        self.assertEqual(follow_count, one_more_follow_count)
