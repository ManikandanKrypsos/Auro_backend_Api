import 'dart:async';
import 'package:aura/app/resources/asset_resources.dart';
import 'package:flutter/material.dart';
import 'package:get/get.dart';

import '../../routes/names.dart';

class SplashScreen extends StatefulWidget {
  const SplashScreen({super.key});

  @override
  State<SplashScreen> createState() => _SplashScreenState();
}

class _SplashScreenState extends State<SplashScreen> {

  @override
  void initState() {
    super.initState();
    navigateToNext();
  }

  void navigateToNext() {
    Future.delayed(const Duration(seconds: 3), () {
      Get.offNamed(PageRoutes.selectRoleScreen); 
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: SafeArea(
        child: Center(
          child: SizedBox(
            child: Image.asset(AssetResources.logo),
          ),
        ),
      ),
    );
  }
}