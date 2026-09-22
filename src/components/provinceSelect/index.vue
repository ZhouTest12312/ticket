<template>
  <el-row :gutter="8" type="flex" justify="space-between" class="select">
    <el-col :lg="8" :md="8" :sm="8" :xs="24">
      <el-select clearable placeholder="省份" v-model="province">
        <el-option
          v-for="item in provincesList"
          :key="item.regionId"
          :value="item.regionId"
          :label="item.name"
        />
      </el-select>
    </el-col>
    <el-col :lg="8" :md="8" :sm="8" :xs="24">
      <el-select
        clearable
        placeholder="城市"
        v-model="city"
        :disabled="!province"
      >
        <el-option
          v-for="item in citiesList"
          :key="item.regionId"
          :value="item.regionId"
          :label="item.name"
        />
      </el-select>
    </el-col>
    <el-col :lg="8" :md="8" :sm="8" :xs="24">
      <el-select clearable placeholder="区域" v-model="area" :disabled="!city">
        <el-option
          v-for="item in areasList"
          :key="item.regionId"
          :value="item.regionId"
          :label="item.name"
        />
      </el-select>
    </el-col>
  </el-row>
</template>

<script setup>
  import { ref, watch, defineEmits, onMounted, onUnmounted } from 'vue';
  import { getAdressList } from '@/api/layout';
  const props = defineProps({
    provinceInit: String,
    cityInit: String,
    areaInit: String
  });

  const province = ref(props?.provinceInit || '');

  const city = ref(props?.cityInit || '');
  const area = ref(props?.areaInit || '');
  if (province.value != '10' && city.value == '108') {
    city.value = '';
  }
  const provincesList = ref([]);
  const citiesList = ref([]);
  const areasList = ref([]);
  const emits = defineEmits(['change']);
  const getRegionName = (list, regionId) => {
    if (!regionId) return '';
    const hit = (list || []).find(
      (item) => String(item.regionId) === String(regionId)
    );
    return hit?.name || '';
  };
  const emitAddressChange = () => {
    emits('change', {
      province: province.value || '',
      city: city.value || '',
      area: area.value || '',
      provinceName: getRegionName(provincesList.value, province.value),
      cityName: getRegionName(citiesList.value, city.value),
      areaName: getRegionName(areasList.value, area.value)
    });
  };
  const reset = () => {
    province.value = '';
    city.value = '';
    area.value = '';
  };
  defineExpose({
    reset
  });
  watch(
    () => province.value,
    async (val) => {
      if (val) {
        const res = await getAdressList(province.value);
        citiesList.value = res.data;
      }
      city.value = '';
      area.value = '';
      emitAddressChange();
    }
  );
  watch(
    () => city.value,
    async (val) => {
      if (val) {
        const res = await getAdressList(city.value);
        areasList.value = res.data;
      }
      area.value = '';
      emitAddressChange();
    }
  );

  watch(
    () => area.value,
    () => {
      emitAddressChange();
    },
    { deep: true }
  );

  onMounted(async () => {
    console.log('props', props);
    if (props.provinceInit && props.cityInit) {
      const cityRes = await getAdressList(props.provinceInit);
      const areaRes = await getAdressList(props.cityInit);
      citiesList.value = cityRes.data;
      areasList.value = areaRes.data;
    }
    const provinceRes = await getAdressList(1);
    provincesList.value = provinceRes.data;
  });

  // 监听props变化，更新组件内部状态并加载对应数据
  watch(() => props.provinceInit, async (newVal) => {
    if (newVal) {
      province.value = newVal;
      // 加载对应的城市数据
      const cityRes = await getAdressList(newVal);
      citiesList.value = cityRes.data;
    }
  });
  
  watch(() => props.cityInit, async (newVal) => {
    if (newVal) {
      city.value = newVal;
      // 加载对应的区域数据
      const areaRes = await getAdressList(newVal);
      areasList.value = areaRes.data;
    }
  });
  
  watch(() => props.areaInit, (newVal) => {
    if (newVal) {
      area.value = newVal;
    }
  });
</script>

<style lang="scss" scoped>
  .select {
    width: -webkit-fill-available;
  }
</style>
