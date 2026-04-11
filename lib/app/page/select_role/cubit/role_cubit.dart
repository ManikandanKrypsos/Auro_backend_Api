import 'package:flutter_bloc/flutter_bloc.dart';

class RoleCubit extends Cubit<Map<String, dynamic>?> {
  RoleCubit() : super(null);

  void selectRole(Map<String, dynamic> role) => emit(role);
}