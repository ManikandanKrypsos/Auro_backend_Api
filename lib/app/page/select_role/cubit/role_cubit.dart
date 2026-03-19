import 'package:flutter_bloc/flutter_bloc.dart';

class RoleCubit extends Cubit<String> {
  RoleCubit() : super('1');

  void selectRole(String roleId) {
    emit(roleId);
  }
}