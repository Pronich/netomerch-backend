from rest_framework import serializers

from apps.products.models import ImageColorItem, Item
from apps.reviews.models import Review
from config import settings


class ItemMainPageSerializer(serializers.ModelSerializer):
    """сериализатор товара для главной страницы api/v1/main/"""
    item_id = serializers.IntegerField(source="id")
    image = serializers.SerializerMethodField()

    class Meta:
        model = Item
        fields = ("item_id", "name", "image")

    def get_image(self, item):
        request = self.context.get('request')
        main_image = ImageColorItem.objects.filter(
            item_id=item.id, is_main_color=True, is_main_image=True).values_list("image", flat=True).first()
        if main_image:
            main_image = f'{settings.MEDIA_URL}{main_image}'
            return request.build_absolute_uri(main_image)


class ReviewMainPageSerializer(serializers.ModelSerializer):
    """сериализатор отзывов для главной страницы"""
    image = serializers.SerializerMethodField()

    class Meta:
        model = Review
        fields = ("id", "text", "author", "image", "item_id")

    def get_image(self, review):
        item = review.item
        request = self.context.get('request')
        main_image = ImageColorItem.objects.filter(
            item_id=item, is_main_color=True, is_main_image=True).values_list("image", flat=True).first()
        if main_image:
            main_image = f'{settings.MEDIA_URL}{main_image}'
            return request.build_absolute_uri(main_image)


class MainPageSerializer(serializers.Serializer):
    """сериализатор для главной страницы - отзывы + популярные (is_hit) товары"""
    popular = ItemMainPageSerializer(many=True)
    reviews = ReviewMainPageSerializer(many=True)
