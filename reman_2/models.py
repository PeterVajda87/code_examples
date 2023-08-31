from django.db import models

class Customer(models.Model):
    customer_name = models.CharField(max_length=32)

class MaterialGroup(models.Model):
    material_group = models.CharField(max_length=32)

class Material(models.Model):
    material_number = models.CharField(max_length=32)
    customer = models.ForeignKey(to=Customer, on_delete=models.SET_NULL, null=True)
    material_group = models.ForeignKey(to=MaterialGroup, on_delete=models.SET_NULL, null=True)
    is_root_material = models.BooleanField(default=False)
    refreshed = models.DateTimeField(blank=True, null=True)

class RootMaterialComposition(models.Model):
    material = models.ForeignKey(to=Material, related_name="root_material", on_delete=models.SET_NULL, null=True)
    compound_material = models.ForeignKey(to=Material, related_name="compound_material", on_delete=models.SET_NULL, null=True)
    compound_material_quantity = models.IntegerField(default=0)
    is_ignored = models.BooleanField(default=False)


class Header(models.Model):
    order = models.CharField(max_length=12, unique=True)
    order_type = models.CharField(max_length=4)
    material_number = models.ForeignKey(to=Material, on_delete=models.SET_NULL, null=True)
    order_quantity = models.FloatField()
    quantity_delivered = models.FloatField()
    rework_quantity = models.FloatField()
    confirmed_scrap = models.FloatField()
    system_status = models.CharField(max_length=128)
    release_date = models.DateField(null=True)
    actual_finish_date = models.DateField(null=True)


class Operation(models.Model):
    order = models.CharField(max_length=12)
    material_number = models.ForeignKey(to=Material, on_delete=models.SET_NULL, null=True)
    activity = models.CharField(max_length=12)
    work_center = models.CharField(max_length=12)
    operation_text = models.CharField(max_length=255)
    operation_quantity = models.FloatField()
    confirmed_yield = models.FloatField()
    scrap = models.FloatField()
    rework_quantity = models.FloatField()


class Component(models.Model):
    order = models.CharField(max_length=12)
    pegged_requirement = models.ForeignKey(to=Material, related_name='pegged_requirement', on_delete=models.SET_NULL, null=True)
    material = models.ForeignKey(to=Material, related_name='material', on_delete=models.SET_NULL, null=True)
    requirement_quantity = models.FloatField()
    quantity_withdrawn = models.FloatField()


class Losses(models.Model):
    order = models.CharField(max_length=12)
    material = models.ForeignKey(to=Material, related_name='losses_material', on_delete=models.SET_NULL, null=True)
    damage = models.CharField(max_length=16)
    assembly = models.ForeignKey(to=Material, related_name='losses_assembly', on_delete=models.SET_NULL, null=True)
    quantity = models.FloatField()


class Yfcorer(models.Model):
    core_shipment_id = models.IntegerField()
    pallet_number = models.IntegerField()
    core_return_item_number = models.IntegerField()
    change_date = models.DateField()
    core_inventory_flag = models.IntegerField()
    material = models.ForeignKey(to=Material, related_name='yfcorer_material', on_delete=models.SET_NULL, null=True)


class SortingResults(models.Model):
    material = models.ForeignKey(to=Material, on_delete=models.SET_NULL, null=True)
    material_group = models.ForeignKey(to=MaterialGroup, on_delete=models.SET_NULL, null=True)
    customer = models.ForeignKey(to=Customer, on_delete=models.SET_NULL, null=True)
    period_start = models.DateField()
    period_end = models.DateField()
    result = models.FloatField()