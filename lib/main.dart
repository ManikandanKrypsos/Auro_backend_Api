import 'package:aura/app/routes/routes.dart';
import 'package:aura/app/theme/color/color.dart';
import 'package:flutter/material.dart';
import 'package:get/route_manager.dart';

import 'app/routes/names.dart';

import 'package:firebase_core/firebase_core.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  await Firebase.initializeApp();
  runApp(const MyApp());
}

class MyApp extends StatelessWidget {
  const MyApp({super.key});

  @override
  Widget build(BuildContext context) {
    return GetMaterialApp(
      title: 'Aura',
      debugShowCheckedModeBanner: false,
             getPages: Routes.routes,
        initialRoute: PageRoutes.splashScreen,

      theme: ThemeData(
         brightness: Brightness.dark,
       scaffoldBackgroundColor: ColorResources.blackColor,
           appBarTheme:  AppBarTheme(
          backgroundColor: ColorResources.blackColor, 
          foregroundColor: ColorResources.whiteColor, 
          elevation: 0,
        ),

        colorScheme: ColorScheme.fromSeed(seedColor: Colors.deepPurple,
         brightness: Brightness.dark,),
        
      ),
  
    );
  }
}

