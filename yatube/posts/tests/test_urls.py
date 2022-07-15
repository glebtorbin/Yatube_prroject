from django.core.cache import cache
from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from http import HTTPStatus

from posts.models import Post, Group

User = get_user_model()


class PostsURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='test_user')
        cls.author = User.objects.create_user(username='author')
        cls.guest_user = Client()
        cls.group = Group.objects.create(slug='test_slug')
        cls.post = Post.objects.create(author=cls.author, id=33)
        cls.templates_url_names = {
            '/': 'posts/index.html',
            '/group/test_slug/': 'posts/group_list.html',
            '/profile/author/': 'posts/profile.html',
            '/posts/33/': 'posts/post_detail.html',
            '/create/': 'posts/create_post.html',
            '/posts/33/edit/': 'posts/create_post.html',
        }

    def setUp(self):
        self.authorized_author = Client()
        self.authorized_author.force_login(self.author)
        self.authorized_user = Client()
        self.authorized_user.force_login(self.user)
        cache.clear()

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        for address, template in self.templates_url_names.items():
            with self.subTest(address=address):
                response = self.authorized_author.get(address)
                self.assertTemplateUsed(response, template)

    def test_posts_pages_response(self):
        """Страницы по адресам create/
        and posts/33/edit перенаправит анонимного
        пользователя на страницу логина и, что эта страница
        доступна авторизованному пользователю и также проверяем доступ
        ко всем остальным станицам"""
        guest_pages = {
            '/': HTTPStatus.OK,
            '/group/test_slug/': HTTPStatus.OK,
            '/profile/author/': HTTPStatus.OK,
            '/posts/33/': HTTPStatus.OK,
            'unexisting_page': HTTPStatus.NOT_FOUND}
        for address, status in guest_pages.items():
            with self.subTest(address=address):
                response = self.guest_user.get(address)
                self.assertEqual(response.status_code, status)
        redirect_pages = {
            '/create/': '/auth/login/?next=/create/',
            '/posts/33/edit/': '/auth/login/?next=/posts/33/edit/'
        }
        for address, page_for_redirect in redirect_pages.items():
            with self.subTest(address=address):
                response = self.guest_user.get(address, follow=True)
                self.assertRedirects(response, page_for_redirect)
                response_1 = self.authorized_author.get(address)
                self.assertEqual(response_1.status_code, 200)
