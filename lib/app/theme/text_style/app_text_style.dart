import 'package:flutter/material.dart';
import '../color/color.dart';

class AppTextStyles {
  AppTextStyles._();

  static const TextStyle headingLarge = TextStyle(
    fontFamily: 'CormorantGaramond',
    color: ColorResources.whiteColor,
    fontWeight: FontWeight.w300,
    fontSize: 40,
    letterSpacing: 4.0,
    height: 1.1,
  );
  static const TextStyle headingMedium = TextStyle(
    fontFamily: 'CormorantGaramond',
    color: ColorResources.primaryColor,
    fontWeight: FontWeight.w300,
    fontSize: 15,
    letterSpacing: 1.0,
    height: 1.1,
  );

  static const TextStyle headingSmall = TextStyle(
    fontFamily: 'CormorantGaramond',
    color: Color(0xB3F1F5F9),
    fontSize: 12,
    fontWeight: FontWeight.w600,
    letterSpacing: 1.5,
  );
  static const TextStyle bodyItalic = TextStyle(
  fontFamily: 'CormorantGaramond',
  color: ColorResources.liteTextColor,
  fontWeight: FontWeight.w300,
  fontStyle: FontStyle.italic,
  fontSize: 13,
  letterSpacing: 0.5,
  height: 1.4,
);
}
