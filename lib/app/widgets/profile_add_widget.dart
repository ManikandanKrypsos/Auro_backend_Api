
import 'package:flutter/material.dart';

import '../theme/color/color.dart';

class ProfileAddWidget extends StatelessWidget {
  const ProfileAddWidget({
    super.key,
  });

  @override
  Widget build(BuildContext context) {
    return Stack(
      children: [
        Container(
          padding: const EdgeInsets.all(3),
          decoration: BoxDecoration(
            shape: BoxShape.circle,
            border: Border.all(
                color: ColorResources.primaryColor, width: 2),
          ),
          child: CircleAvatar(
            radius: 64,
            backgroundColor: ColorResources.cardColor,
            backgroundImage:
                const AssetImage('assets/images/therapist1.jpg'),
            onBackgroundImageError: (_, __) {},
            child: const Icon(Icons.person,
                color: ColorResources.borderColor, size: 48),
          ),
        ),
        Positioned(
          bottom: 4,
          right: 4,
          child: Container(
            padding: const EdgeInsets.all(4),
            decoration: BoxDecoration(
              color: ColorResources.primaryColor,
              shape: BoxShape.circle,
              border: Border.all(
                  color: ColorResources.blackColor, width: 2),
            ),
            child: const Icon(Icons.add_a_photo,
                color: Colors.black, size: 14),
          ),
        ),
      ],
    );
  }
}