<template>
  <div class="box">
    <div class="bgImg">
      <div class="text"></div>
      <img src="/src/assets/welcome.jpg" />
    </div>
  </div>
</template>
<script setup name="Index">
  
</script>
<style lang="scss" scoped>
  .box {
    width: 100%;
    height: calc(100vh - 90px);
    display: table;
    width: 100%;
    .bgImg {
      display: table-cell;
      vertical-align: middle;
      text-align: center;
      background-color: #ffffff;

      img {
        width: 50%;
        object-fit: contain;
      }
    }
  }
  .text {
    font-family:
      PingFangSC,
      PingFang SC;
    font-weight: 500;
    font-size: 22px;
    color: #444067;
    line-height: 22px;
    letter-spacing: 2px;
    padding-right: 156px;
  }
</style>
